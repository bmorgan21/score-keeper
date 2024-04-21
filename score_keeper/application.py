import datetime as dt
import urllib.parse
from uuid import uuid4

import humanize
import markdown
from markupsafe import Markup
from pydantic_core import ValidationError
from quart import Quart, has_request_context, redirect, request, url_for
from quart.templating import render_template
from quart_auth import QuartAuth, Unauthorized
from quart_schema import QuartSchema
from quart_schema.extension import (
    QUART_SCHEMA_OPERATION_ID_ATTRIBUTE,
    QUART_SCHEMA_TAG_ATTRIBUTE,
)
from quart_schema.validation import (
    RequestSchemaValidationError,
    ResponseSchemaValidationError,
)
from tortoise.contrib.quart import register_tortoise
from werkzeug.exceptions import NotFound

from score_keeper import schemas, settings
from score_keeper.command import register_commands
from score_keeper.lib.auth import AuthUser, Forbidden
from score_keeper.lib.error import ActionError, ForbiddenActionError
from score_keeper.lib.middleware import ProxyMiddleware
from score_keeper.lib.pubsub import RedisPubSubManager
from score_keeper.lib.websocket import WebsocketManager
from score_keeper.log import register_logging


def relative_url_for(**params):
    query_args = urllib.parse.parse_qs(request.query_string.decode("utf-8"))
    query_args.update(params)

    return url_for(request.url_rule.endpoint, **request.view_args, **query_args)


def utc_to_local(value):
    offset = None
    if "tz" in request.cookies:
        try:
            offset = int(request.cookies["tz"])
        except ValueError:
            offset = None

    if offset:
        return (value - dt.timedelta(seconds=offset)).replace(tzinfo=None)

    return value


def register_blueprints(app):
    # pylint: disable=import-outside-toplevel
    from score_keeper.blueprints.api import blueprint as api_blueprint
    from score_keeper.blueprints.auth import blueprint as auth_blueprint
    from score_keeper.blueprints.auth_google import blueprint as auth_google_blueprint
    from score_keeper.blueprints.chat import blueprint as chat_blueprint
    from score_keeper.blueprints.event import blueprint as event_blueprint
    from score_keeper.blueprints.marketing import blueprint as marketing_blueprint
    from score_keeper.blueprints.post import blueprint as post_blueprint
    from score_keeper.blueprints.user import blueprint as user_blueprint

    # pylint: enable=import-outside-toplevel

    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(auth_google_blueprint, url_prefix="/auth/google")
    app.register_blueprint(chat_blueprint, url_prefix="/chat")
    app.register_blueprint(event_blueprint, url_prefix="/event")
    app.register_blueprint(marketing_blueprint)
    app.register_blueprint(post_blueprint, url_prefix="/post")
    app.register_blueprint(user_blueprint, url_prefix="/user")


class MyQuartAuth(QuartAuth):
    def resolve_user(self) -> AuthUser:
        auth_id = self.load_cookie()
        if auth_id is None:
            auth_id = self.load_bearer()

        return self.user_class(auth_id)


def create_app(**config_overrides):
    app = Quart(__name__, static_folder="static")
    app.asgi_app = ProxyMiddleware(app.asgi_app)

    app.config.from_object(settings)
    app.config.update(config_overrides)

    QuartSchema(app)
    auth_manager = MyQuartAuth(app)
    auth_manager.user_class = AuthUser

    register_logging(app)
    register_blueprints(app)
    register_tortoise(app, config=app.config["TORTOISE_ORM"])
    register_commands(app)

    pubsub_client = RedisPubSubManager("redis")
    app.socket_manager = WebsocketManager(pubsub_client)

    # hide routes that don't have tags
    for rule in app.url_map.iter_rules():
        func = app.view_functions[rule.endpoint]

        if not rule.endpoint.startswith("api."):
            func.__dict__["_quart_schema_hidden"] = True
        else:
            tag = rule.endpoint.split(".")[1]
            setattr(func, QUART_SCHEMA_TAG_ATTRIBUTE, set([tag]))

            operation_id = rule.endpoint[4:].replace(".", "_")
            setattr(func, QUART_SCHEMA_OPERATION_ID_ATTRIBUTE, operation_id)

            d = getattr(func, "_quart_schema_response_schemas")
            d[422] = (schemas.Errors, None)
            d[404] = (schemas.Error, None)

    @app.errorhandler(RequestSchemaValidationError)
    async def handle_request_validation_error(error):
        if isinstance(error.validation_error, ValidationError):
            return (
                schemas.Errors(
                    errors=[
                        schemas.Error(
                            loc=".".join([str(y) for y in x.get("loc", [])]),
                            type=x.get("type"),
                            msg=x["msg"],
                            input=x.get("input"),
                        )
                        for x in error.validation_error.errors()
                    ]
                ),
                422,
            )
        return (
            schemas.Errors(
                errors=[schemas.Error(loc="page", type="VALIDATION", msg=str(error))]
            ),
            422,
        )

    @app.errorhandler(ResponseSchemaValidationError)
    async def handle_response_validation_error(error):
        if isinstance(error.validation_error, ValidationError):
            return (
                schemas.Errors(
                    errors=[
                        schemas.Error(
                            loc=".".join([str(y) for y in x.get("loc", [])]),
                            type=x.get("type"),
                            msg=x["msg"],
                            input=x.get("input"),
                        )
                        for x in error.validation_error.errors()
                    ]
                ),
                422,
            )

        return (
            schemas.Errors(
                errors=[
                    schemas.Error(
                        loc="page", type="VALIDATION", msg="Invalid Response Type"
                    )
                ]
            ),
            422,
        )

    @app.errorhandler(ActionError)
    async def handle_field_value_error(error):
        if error.type in ("action_error.not_found", "action_error.does_not_exist"):
            return (
                schemas.Error(loc=error.loc, type=error.type, msg=str(error)),
                404,
            )

        return (
            schemas.Errors(
                errors=[schemas.Error(loc=error.loc, type=error.type, msg=str(error))]
            ),
            422,
        )

    @app.errorhandler(Unauthorized)
    async def handle_response_unathorized_error(error):
        if has_request_context() and request.accept_mimetypes.accept_html:
            return redirect(url_for("auth.login", r=request.url))

        return (
            schemas.Error(loc="auth_id", type="auth.unauthorized", msg=str(error)),
            401,
        )

    @app.errorhandler(Forbidden)
    @app.errorhandler(ForbiddenActionError)
    async def handle_response_forbidden_error(error):
        if has_request_context() and request.accept_mimetypes.accept_html:
            return await render_template("403.html")

        return (
            schemas.Error(loc="auth_id", type="auth.forbidden", msg=str(error)),
            403,
        )

    @app.errorhandler(NotFound)
    async def handle_response_not_found_error(error):
        if has_request_context() and request.accept_mimetypes.accept_html:
            return await render_template("404.html")

        return (
            schemas.Error(loc="page", type="NOT_FOUND", msg=str(error)),
            404,
        )

    @app.template_filter(name="ago")
    def ago_filter(value, default=""):
        if value:
            now = dt.datetime.now(dt.timezone.utc)
            delta = now - value
            if delta > dt.timedelta(days=1):
                value = utc_to_local(value)
                return value.strftime("%b %d, %Y")
            return humanize.naturaltime(delta)
        return default

    @app.template_filter(name="markdown")
    def markdown_filter(value):
        return Markup(markdown.markdown(value))

    @app.template_filter(name="format_datetime")
    def format_datetime(value, format="%m/%d/%Y %H:%M:%S"):
        value = utc_to_local(value)
        return value.strftime(format)

    @app.template_filter(name="none_to_empty")
    def none_to_empty(value):
        if value is None:
            return ""
        return value

    @app.context_processor
    def add_context():
        return {"relative_url_for": relative_url_for, "uuid4": uuid4}

    return app
