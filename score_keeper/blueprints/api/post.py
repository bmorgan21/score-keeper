from quart import Blueprint
from quart_auth import current_user, login_required
from quart_schema import validate_querystring, validate_request, validate_response
from tortoise.transactions import atomic

from score_keeper import actions, schemas

blueprint = Blueprint("post", __name__)


@blueprint.post("")
@validate_request(schemas.PostCreate)
@validate_response(schemas.Post, 201)
@atomic()
@login_required
async def create(data: schemas.PostCreate) -> schemas.Post:
    return await actions.post.create(await current_user.get_user(), data), 201


@blueprint.get("/<int:id>")
@validate_querystring(schemas.PostGetOptions)
@validate_response(schemas.Post, 200)
@atomic()
@login_required
async def read(id: int, query_args: schemas.PostGetOptions) -> schemas.Post:
    return (
        await actions.post.get(
            await current_user.get_user(), id=id, options=query_args
        ),
        200,
    )


@blueprint.get("")
@validate_querystring(schemas.PostQueryString)
@validate_response(schemas.PostResultSet, 200)
@atomic()
@login_required
async def read_many(query_args: schemas.PostQueryString) -> schemas.PostResultSet:
    return await actions.post.query(
        await current_user.get_user(), query_args.to_query()
    )


@blueprint.patch("/<int:id>")
@validate_request(schemas.PostPatch)
@validate_response(schemas.Post, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.PostPatch) -> schemas.Post:
    return await actions.post.update(await current_user.get_user(), id, data)


@blueprint.delete("/<int:id>")
@validate_response(schemas.DeleteConfirmed, 200)
@atomic()
@login_required
async def delete(id: int) -> schemas.DeleteConfirmed:
    await actions.post.delete(await current_user.get_user(), id)

    return schemas.DeleteConfirmed(id=id)


@blueprint.put("/<int:id>/like")
@validate_response(schemas.PostLike, 200)
@atomic()
@login_required
async def like(id: int) -> schemas.PostLike:
    return await actions.post.like(await current_user.get_user(), id)


@blueprint.delete("/<int:id>/like")
@validate_response(schemas.DeleteConfirmed, 200)
@atomic()
@login_required
async def unlike(id: int) -> schemas.PostLike:
    await actions.post.unlike(await current_user.get_user(), id)

    return schemas.DeleteConfirmed(id=id)
