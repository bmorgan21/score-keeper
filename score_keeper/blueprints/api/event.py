from quart import Blueprint
from quart_auth import current_user, login_required
from quart_schema import validate_querystring, validate_request, validate_response
from tortoise.transactions import atomic

from score_keeper import actions, schemas

blueprint = Blueprint("event", __name__)


@blueprint.post("")
@validate_request(schemas.EventCreate)
@validate_response(schemas.Event, 201)
@atomic()
@login_required
async def create(data: schemas.EventCreate) -> schemas.Event:
    return await actions.event.create(await current_user.get_user(), data), 201


@blueprint.get("/<int:id>")
@validate_querystring(schemas.EventGetOptions)
@validate_response(schemas.Event, 200)
@atomic()
@login_required
async def read(id: int, query_args: schemas.EventGetOptions) -> schemas.Event:
    return (
        await actions.event.get(
            await current_user.get_user(), id=id, options=query_args
        ),
        200,
    )


@blueprint.get("")
@validate_querystring(schemas.EventQueryString)
@validate_response(schemas.EventResultSet, 200)
@atomic()
@login_required
async def read_many(query_args: schemas.EventQueryString) -> schemas.EventResultSet:
    return await actions.event.query(
        await current_user.get_user(), query_args.to_query()
    )


@blueprint.patch("/<int:id>")
@validate_request(schemas.EventPatch)
@validate_response(schemas.Event, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.EventPatch) -> schemas.Event:
    return await actions.event.update(await current_user.get_user(), id, data)


@blueprint.delete("/<int:id>")
@validate_response(schemas.DeleteConfirmed, 200)
@atomic()
@login_required
async def delete(id: int) -> schemas.DeleteConfirmed:
    await actions.event.delete(await current_user.get_user(), id)

    return schemas.DeleteConfirmed(id=id)


@blueprint.post("/<int:id>/score")
@validate_request(schemas.EventScoreCreate)
@validate_response(schemas.Event, 201)
@atomic()
@login_required
async def score(id: int, data: schemas.EventScoreCreate) -> schemas.Event:
    return await actions.event.score(await current_user.get_user(), id, data), 201
