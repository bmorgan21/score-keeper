from quart import Blueprint
from quart_auth import current_user, login_required
from quart_schema import validate_querystring, validate_request, validate_response
from tortoise.transactions import atomic

from score_keeper import actions, schemas

blueprint = Blueprint("user", __name__)


@blueprint.post("")
@validate_request(schemas.UserCreate)
@validate_response(schemas.User, 200)
@atomic()
@login_required
async def create(data: schemas.UserCreate) -> schemas.User:
    return await actions.user.create(await current_user.get_user(), data)


@blueprint.get("/<int:id>")
@validate_querystring(schemas.UserGetOptions)
@validate_response(schemas.User, 200)
@atomic()
@login_required
async def read(id: int, query_args: schemas.UserGetOptions) -> schemas.User:
    return (
        await actions.user.get(
            await current_user.get_user(), id=id, options=query_args
        ),
        200,
    )


@blueprint.get("")
@validate_querystring(schemas.UserQueryString)
@validate_response(schemas.UserResultSet, 200)
@atomic()
@login_required
async def read_many(query_args: schemas.UserQueryString) -> schemas.UserResultSet:
    return await actions.user.query(
        await current_user.get_user(), query_args.to_query()
    )


@blueprint.patch("/<int:id>")
@validate_request(schemas.UserPatch)
@validate_response(schemas.User, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.UserPatch) -> schemas.User:
    return await actions.user.update(await current_user.get_user(), id, data)
