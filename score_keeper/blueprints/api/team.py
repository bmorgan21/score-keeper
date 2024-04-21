from quart import Blueprint
from quart_auth import current_user, login_required
from quart_schema import validate_querystring, validate_request, validate_response
from tortoise.transactions import atomic

from score_keeper import actions, schemas

blueprint = Blueprint("team", __name__)


@blueprint.post("")
@validate_request(schemas.TeamCreate)
@validate_response(schemas.Team, 201)
@atomic()
@login_required
async def create(data: schemas.TeamCreate) -> schemas.Team:
    return await actions.team.create(await current_user.get_user(), data), 201


@blueprint.get("/<int:id>")
@validate_querystring(schemas.TeamGetOptions)
@validate_response(schemas.Team, 200)
@atomic()
@login_required
async def read(id: int, query_args: schemas.TeamGetOptions) -> schemas.Team:
    return (
        await actions.team.get(
            await current_user.get_user(), id=id, options=query_args
        ),
        200,
    )


@blueprint.get("")
@validate_querystring(schemas.TeamQueryString)
@validate_response(schemas.TeamResultSet, 200)
@atomic()
@login_required
async def read_many(query_args: schemas.TeamQueryString) -> schemas.TeamResultSet:
    return await actions.team.query(
        await current_user.get_user(), query_args.to_query()
    )


@blueprint.patch("/<int:id>")
@validate_request(schemas.TeamPatch)
@validate_response(schemas.Team, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.TeamPatch) -> schemas.Team:
    return await actions.team.update(await current_user.get_user(), id, data)


@blueprint.delete("/<int:id>")
@validate_response(schemas.DeleteConfirmed, 200)
@atomic()
@login_required
async def delete(id: int) -> schemas.DeleteConfirmed:
    await actions.team.delete(await current_user.get_user(), id)

    return schemas.DeleteConfirmed(id=id)
