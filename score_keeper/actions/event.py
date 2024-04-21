import json
from typing import Union

from score_keeper import enums, models, schemas
from score_keeper.lib.error import ActionError, ForbiddenActionError
from score_keeper.lib.message_manager import MessageManager

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
    user: schemas.User, id: int = None, options: schemas.EventGetOptions = None
) -> schemas.Event:
    event = None
    if id:
        event = await models.Event.get(id=id)
    else:
        raise ActionError("missing lookup key", type="not_found")

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.READ
    ):
        raise ForbiddenActionError()

    if options:
        if options.resolves:
            await event.fetch_related(*options.resolves)

    return schemas.Event.model_validate(event)


@handle_orm_errors
async def query(_: schemas.User, q: schemas.EventQuery) -> schemas.EventResultSet:
    qs = models.Event.all()

    queryset, pagination = await q.apply(qs)

    return schemas.EventResultSet(
        pagination=pagination,
        events=[schemas.Event.model_validate(event) for event in await queryset],
    )


@handle_orm_errors
async def create(user: schemas.User, data: schemas.EventCreate) -> schemas.Event:
    if not has_permission(user, None, enums.Permission.CREATE):
        raise ForbiddenActionError()

    event = await models.Event.create(season=data.season, created_by_id=user.id)

    await event.save()

    await competitor_create(
        user, event.id, schemas.CompetitorCreate(home_away=enums.HomeAway.AWAY)
    )
    await competitor_create(
        user, event.id, schemas.CompetitorCreate(home_away=enums.HomeAway.HOME)
    )

    return schemas.Event.model_validate(event)


@handle_orm_errors
async def delete(user: schemas.User, id: int) -> None:
    event = await models.Event.get(id=id)

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.DELETE
    ):
        raise ForbiddenActionError()

    await event.delete()


@handle_orm_errors
async def update(
    user: schemas.User, id: int, data: schemas.EventPatch
) -> schemas.Event:
    event = await models.Event.get(id=id)

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    conditional_set(event, "season", data.season)
    conditional_set(event, "period", data.period)

    if data.status != schemas.NOTSET:
        event.update_status(data.status)

    await event.save()

    return schemas.Event.model_validate(event)


@handle_orm_errors
async def competitor_create(
    user: schemas.User, id: int, data: schemas.CompetitorCreate
) -> schemas.Competitor:
    event = await models.Event.get(id=id)

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    competitor = await models.Competitor.create(
        event_id=id, team_id=data.team_id, home_away=data.home_away
    )

    return schemas.Competitor.model_validate(competitor)


@handle_orm_errors
async def competitor_update(
    user: schemas.User, id: int, competitor_id: int, data: schemas.CompetitorPatch
) -> schemas.Competitor:
    event = await models.Event.get(id=id)

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    competitor = await models.Competitor.get(id=competitor_id)

    conditional_set(competitor, "home_away", data.home_away)
    conditional_set(competitor, "team_id", data.team_id)
    conditional_set(competitor, "score", data.score)

    await competitor.save()

    event = get(
        user, id, options=schemas.EventGetOptions(resolves=["competitors__team"])
    )

    mm = MessageManager(user, f"event-{event.id}")
    await mm.send_message(
        "update",
        f"Event {event.id} updated",
        data=json.loads(schemas.Event.model_dump_json(event)),
    )

    return schemas.Competitor.model_validate(competitor)
