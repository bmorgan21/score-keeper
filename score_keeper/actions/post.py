from typing import Union

from tortoise.exceptions import DoesNotExist
from tortoise.expressions import F, Q

from score_keeper import enums, models, schemas
from score_keeper.lib.error import ActionError, ForbiddenActionError

from .helpers import conditional_set, handle_orm_errors


def has_permission(
    user: schemas.User,
    obj: Union[schemas.Post, None],
    permission: enums.Permission,
) -> bool:
    if permission == enums.Permission.CREATE:
        return True

    if permission == enums.Permission.READ:
        if user.role == enums.UserRole.ADMIN:
            return True
        if user.id == obj.author_id:
            return True
        return obj.status == enums.PostStatus.PUBLISHED

    if permission == enums.Permission.UPDATE:
        if user.role == enums.UserRole.ADMIN:
            return True
        if user.id == obj.author_id:
            return True
        return False

    if permission == enums.Permission.DELETE:
        if user.role == enums.UserRole.ADMIN:
            return True
        if user.id == obj.author_id:
            return True
        return False

    return False


@handle_orm_errors
async def get(
    user: schemas.User, id: int = None, options: schemas.PostGetOptions = None
) -> schemas.Post:
    post = None
    if id:
        post = await models.Post.get(id=id)
    else:
        raise ActionError("missing lookup key", type="not_found")

    if not has_permission(
        user, schemas.Post.model_validate(post), enums.Permission.READ
    ):
        raise ForbiddenActionError()

    if options:
        if options.resolves:
            await post.fetch_related(*options.resolves)

    return schemas.Post.model_validate(post)


@handle_orm_errors
async def query(user: schemas.User, q: schemas.PostQuery) -> schemas.PostResultSet:
    qs = models.Post.all()
    if user.role != enums.UserRole.ADMIN:
        qs = qs.filter(Q(_status=enums.PostStatus.PUBLISHED) | Q(author_id=user.id))

    queryset, pagination = await q.apply(qs)

    return schemas.PostResultSet(
        pagination=pagination,
        posts=[schemas.Post.model_validate(post) for post in await queryset],
    )


@handle_orm_errors
async def create(user: schemas.User, data: schemas.PostCreate) -> schemas.Post:
    if not has_permission(user, None, enums.Permission.CREATE):
        raise ForbiddenActionError()

    post = await models.Post.create(
        title=data.title, content=data.content, author_id=user.id
    )

    post.update_status(data.status)
    await post.save()

    return schemas.Post.model_validate(post)


@handle_orm_errors
async def delete(user: schemas.User, id: int) -> None:
    post = await models.Post.get(id=id)

    if not has_permission(
        user, schemas.Post.model_validate(post), enums.Permission.DELETE
    ):
        raise ForbiddenActionError()

    await post.delete()


@handle_orm_errors
async def update(user: schemas.User, id: int, data: schemas.PostPatch) -> schemas.Post:
    post = await models.Post.get(id=id)

    if not has_permission(
        user, schemas.Post.model_validate(post), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    conditional_set(post, "title", data.title)
    conditional_set(post, "content", data.content)

    if data.status != schemas.NOTSET:
        post.update_status(data.status)

    await post.save()

    return schemas.Post.model_validate(post)


@handle_orm_errors
async def view(_: schemas.User, id: int) -> None:
    await models.Post.filter(id=id).update(viewed=F("viewed") + 1)


@handle_orm_errors
async def get_like(user: schemas.User, id: int) -> schemas.PostLike:
    post_like = await models.PostLike.get(post_id=id, user_id=user.id)
    return schemas.PostLike.model_validate(post_like)


@handle_orm_errors
async def like(user: schemas.User, id: int) -> schemas.PostLike:
    post = await models.Post.get(id=id)

    if not has_permission(
        user, schemas.Post.model_validate(post), enums.Permission.READ
    ):
        raise ForbiddenActionError()

    try:
        post_like = await models.PostLike.get(post_id=id, user_id=user.id)
    except DoesNotExist:
        post_like = await models.PostLike.create(post_id=id, user_id=user.id)

    return schemas.PostLike.model_validate(post_like)


@handle_orm_errors
async def unlike(user: schemas.User, id: int) -> None:
    post = await models.Post.get(id=id)

    if not has_permission(
        user, schemas.Post.model_validate(post), enums.Permission.READ
    ):
        raise ForbiddenActionError()

    try:
        post_like = await models.PostLike.get(post_id=id, user_id=user.id)
    except DoesNotExist:
        pass
    else:
        await post_like.delete()
