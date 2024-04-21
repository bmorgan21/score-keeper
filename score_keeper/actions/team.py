from typing import Union

from score_keeper import enums, models, schemas
from score_keeper.lib.error import ActionError, ForbiddenActionError

from .helpers import conditional_set, handle_orm_errors


def has_permission(
    user: schemas.User,
    obj: Union[schemas.Event, None],
    permission: enums.Permission,
) -> bool:
    if permission == enums.Permission.CREATE:
        return True

    if permission == enums.Permission.READ:
        return True

    if permission == enums.Permission.UPDATE:
        if user.role == enums.UserRole.ADMIN:
            return True
        if user.id == obj.created_by_id:
            return True
        return False

    if permission == enums.Permission.DELETE:
        if user.role == enums.UserRole.ADMIN:
            return True
        if user.id == obj.created_by_id:
            return True
        return False

    return False


@handle_orm_errors
async def get(
    user: schemas.User, id: int = None, options: schemas.TeamGetOptions = None
) -> schemas.Team:
    team = None
    if id:
        team = await models.Team.get(id=id)
    else:
        raise ActionError("missing lookup key", type="not_found")

    if not has_permission(
        user, schemas.Team.model_validate(team), enums.Permission.READ
    ):
        raise ForbiddenActionError()

    if options:
        if options.resolves:
            await team.fetch_related(*options.resolves)

    return schemas.Team.model_validate(team)


@handle_orm_errors
async def query(_: schemas.User, q: schemas.TeamQuery) -> schemas.TeamResultSet:
    qs = models.Team.all()

    queryset, pagination = await q.apply(qs)

    return schemas.TeamResultSet(
        pagination=pagination,
        teams=[schemas.Team.model_validate(team) for team in await queryset],
    )


@handle_orm_errors
async def create(user: schemas.User, data: schemas.TeamCreate) -> schemas.Team:
    if not has_permission(user, None, enums.Permission.CREATE):
        raise ForbiddenActionError()

    team = await models.Team.create(name=data.name, created_by_id=user.id)

    await team.save()

    return schemas.Team.model_validate(team)


@handle_orm_errors
async def delete(user: schemas.User, id: int) -> None:
    team = await models.Team.get(id=id)

    if not has_permission(
        user, schemas.Team.model_validate(team), enums.Permission.DELETE
    ):
        raise ForbiddenActionError()

    await team.delete()


@handle_orm_errors
async def update(user: schemas.User, id: int, data: schemas.TeamPatch) -> schemas.Team:
    team = await models.Team.get(id=id)

    if not has_permission(
        user, schemas.Team.model_validate(team), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    conditional_set(team, "name", data.name)

    await team.save()

    return schemas.Team.model_validate(team)
