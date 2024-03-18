from quart import Blueprint, current_app
from quart_auth import login_user
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic
from unique_names_generator import get_random_name
from unique_names_generator.data import ADJECTIVES, ANIMALS

from score_keeper import actions, enums, schemas
from score_keeper.lib.auth import AuthUser
from score_keeper.lib.error import ActionError

blueprint = Blueprint("auth", __name__)


@blueprint.post("/token")
@validate_request(schemas.AuthTokenCreate)
@validate_response(schemas.TokenCreateSuccess, 200)
@atomic()
async def token_create(data: schemas.AuthTokenCreate) -> schemas.TokenCreateSuccess:
    user = None
    try:
        user = await actions.user.get(schemas.User.system_user(), email=data.email)
    except ActionError as error:
        if error.type != "action_error.does_not_exist":
            raise

    if user and await actions.user.check_password(user.id, data.password):
        token = await actions.token.create(
            user, enums.TokenType.WEB, schemas.TokenCreate(name="Web Login")
        )

        login_user(AuthUser(token.auth_id))

        token.auth_id = current_app.extensions["QUART_AUTH"][0].dump_token(
            token.auth_id
        )

        return token

    raise ActionError("invalid email or password", loc="password")


@blueprint.post("/user")
@validate_request(schemas.AuthUserCreate)
@validate_response(schemas.User, 200)
@atomic()
async def user_create(data: schemas.AuthUserCreate) -> schemas.User:
    name = get_random_name(combo=[ADJECTIVES, ANIMALS], style="lowercase")

    user = await actions.user.create(
        schemas.User.system_user(),
        schemas.UserCreate(name=name, email=data.email, password=data.password),
    )

    token = await actions.token.create(
        user, enums.TokenType.WEB, schemas.TokenCreate(name="Web Login")
    )

    login_user(AuthUser(token.auth_id))
    return user
