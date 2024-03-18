from quart import Blueprint, current_app
from quart_auth import current_user, login_required
from quart_schema import validate_querystring, validate_request, validate_response
from tortoise.transactions import atomic

from score_keeper import actions, enums, schemas

blueprint = Blueprint("token", __name__)


@blueprint.post("")
@validate_request(schemas.TokenCreate)
@validate_response(schemas.TokenCreateSuccess, 200)
@atomic()
@login_required
async def create(data: schemas.TokenCreate) -> schemas.TokenCreateSuccess:
    user = await current_user.get_user()
    token = await actions.token.create(user, enums.TokenType.API, data)

    token.auth_id = current_app.extensions["QUART_AUTH"][0].dump_token(token.auth_id)

    return token


@blueprint.get("/<int:id>")
@validate_querystring(schemas.TokenGetOptions)
@validate_response(schemas.Token, 200)
@atomic()
@login_required
async def read(id: int, query_args: schemas.TokenGetOptions) -> schemas.Token:
    return (
        await actions.token.get(
            await current_user.get_user(), id=id, options=query_args
        ),
        200,
    )


@blueprint.get("")
@validate_querystring(schemas.TokenQueryString)
@validate_response(schemas.TokenResultSet, 200)
@atomic()
@login_required
async def read_many(query_args: schemas.TokenQueryString) -> schemas.TokenResultSet:
    return await actions.token.query(
        await current_user.get_user(), query_args.to_query()
    )


@blueprint.patch("/<int:id>")
@validate_request(schemas.TokenPatch)
@validate_response(schemas.Token, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.TokenPatch) -> schemas.Token:
    return await actions.token.update(await current_user.get_user(), id, data)
