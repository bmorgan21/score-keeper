import uuid
from typing import Union

from score_keeper import enums, models, schemas
from score_keeper.lib.error import ActionError, ForbiddenActionError

from .helpers import conditional_set, handle_orm_errors


def has_permission(
    user: schemas.User,
    obj: Union[schemas.Token, None],
    permission: enums.Permission,
) -> bool:
    if permission == enums.Permission.CREATE:
        return True

    if permission == enums.Permission.READ:
        if user.role == enums.UserRole.ADMIN:
            return True
        if user.id == obj.user_id:
            return True
        return False

    if permission == enums.Permission.UPDATE:
        if user.role == enums.UserRole.ADMIN:
            return True
        if user.id == obj.user_id:
            return True
        return False

    if permission == enums.Permission.DELETE:
        if user.role == enums.UserRole.ADMIN:
            return True
        if user.id == obj.user_id:
            return True
        return False

    return False


@handle_orm_errors
async def get(
    user: schemas.User,
    id: int = None,
    auth_id: int = None,
    options: schemas.TokenGetOptions = None,
) -> schemas.Post:
    token = None
    if id:
        token = await models.Token.get(id=id)
    elif auth_id:
        token = await models.Token.get(auth_id=auth_id)
    else:
        raise ActionError("missing lookup key", type="not_found")

    if not has_permission(
        user, schemas.Token.model_validate(token), enums.Permission.READ
    ):
        raise ForbiddenActionError()

    if options:
        if options.resolves:
            await token.fetch_related(*options.resolves)

    return schemas.Token.model_validate(token)


@handle_orm_errors
async def query(user: schemas.User, q: schemas.TokenQuery) -> schemas.TokenResultSet:
    qs = models.Token.all()
    if user.role != enums.UserRole.ADMIN:
        qs = qs.filter(user_id=user.id)

    queryset, pagination = await q.apply(qs)

    return schemas.TokenResultSet(
        pagination=pagination,
        tokens=[schemas.Token.model_validate(token) for token in await queryset],
    )


@handle_orm_errors
async def create(
    user: schemas.User, type: enums.TokenType, data: schemas.TokenCreate
) -> schemas.TokenCreateSuccess:
    if not has_permission(user, None, enums.Permission.CREATE):
        raise ForbiddenActionError()

    token = await models.Token.create(
        type=type, name=data.name, auth_id=str(uuid.uuid4()), user_id=user.id
    )

    await token.save()

    return schemas.TokenCreateSuccess.model_validate(token)


@handle_orm_errors
async def delete(user: schemas.User, id: int) -> None:
    token = await models.Token.get(id=id)

    if not has_permission(
        user, schemas.Token.model_validate(token), enums.Permission.DELETE
    ):
        raise ForbiddenActionError()

    await token.delete()


@handle_orm_errors
async def update(user: schemas.User, id: int, data: schemas.TokenPatch) -> schemas.Post:
    token = await models.Token.get(id=id)

    if not has_permission(
        user, schemas.Token.model_validate(token), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    conditional_set(token, "name", data.name)

    await token.save()

    return schemas.Token.model_validate(token)
