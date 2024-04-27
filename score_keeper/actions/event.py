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

    event = await models.Event.create(
        season=data.season, datetime=data.datetime, created_by_id=user.id
    )

    await event.save()

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
    conditional_set(event, "datetime", data.datetime)
    conditional_set(event, "away_team_id", data.away_team_id)
    conditional_set(event, "away_score", data.away_score)
    conditional_set(event, "home_team_id", data.home_team_id)
    conditional_set(event, "home_score", data.home_score)

    if data.status != schemas.NOTSET:
        event.update_status(data.status)

    await event.save()

    schema_event = schemas.Event.model_validate(event)

    mm = MessageManager(user, f"event-{id}")
    await mm.send_message(
        "update",
        f"Event {id} updated",
        data=json.loads(schemas.Event.model_dump_json(schema_event)),
    )

    return schema_event


@handle_orm_errors
async def score(
    user: schemas.User, id: int, data: schemas.EventScoreCreate
) -> schemas.Event:
    event = await models.Event.get(id=id)

    if not has_permission(
        user, schemas.Event.model_validate(event), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    event.away_score = data.away_score
    event.home_score = data.home_score
    await event.save()

    event_score = await models.EventScore.create(
        away_score=data.away_score, home_score=data.home_score, event_id=event.id
    )

    conditional_set(event_score, "away_delta", data.away_delta)
    conditional_set(event_score, "home_delta", data.home_delta)
    conditional_set(event_score, "comment", data.comment)

    await event_score.save()

    schema_event = schemas.Event.model_validate(event)

    mm = MessageManager(user, f"event-{id}")
    await mm.send_message(
        "update",
        f"Event {id} updated",
        data=json.loads(schemas.Event.model_dump_json(schema_event)),
    )

    return schema_event
