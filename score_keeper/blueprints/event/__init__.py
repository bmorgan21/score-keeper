import asyncio
import datetime
import json
import uuid
from typing import Any

from quart import Blueprint, current_app, redirect, request, url_for, websocket
from quart.templating import render_template
from quart_auth import current_user, login_required
from quart_schema import validate_querystring

from score_keeper import actions, enums, schemas
from score_keeper.lib.auth import Forbidden
from score_keeper.lib.error import ActionError
from score_keeper.lib.message_manager import MessageManager

blueprint = Blueprint("event", __name__, template_folder="templates")


@blueprint.route("/")
@validate_querystring(schemas.EventQueryString)
async def index(query_args: schemas.EventQueryString):
    user = await current_user.get_user()
    resultset = await actions.event.query(
        user, query_args.to_query(resolves=["created_by", "away_team", "home_team"])
    )

    subtab = query_args.status
    if query_args.created_by_id == user.id:
        subtab = f"mine-{subtab}"

    return await render_template(
        "event/index.html", resultset=resultset, tab="event", subtab=subtab
    )


@blueprint.route("/<int:id>")
async def view(id: int):
    user = await current_user.get_user()
    event = await actions.event.get(
        user,
        id=id,
        options=schemas.EventGetOptions(resolves=["away_team", "home_team"]),
    )

    can_edit = actions.event.has_permission(user, event, enums.Permission.UPDATE)

    return await render_template("event/view.html", event=event, can_edit=can_edit)


@blueprint.route("/create/")
@login_required
async def create():
    user = await current_user.get_user()
    if not actions.event.has_permission(user, None, enums.Permission.CREATE):
        raise Forbidden()

    now = datetime.datetime.now(datetime.UTC)

    event = schemas.Object()
    event.season = now.year

    modal = 1 if "modal" in request.args else None

    return await render_template(
        "event/create.html",
        status_options=[(x.value.title(), x.value) for x in enums.EventStatus],
        r=url_for(".index", status="{-status-}", author_id=user.id),
        tab="event",
        event=event,
        base_template="modal_base.html" if modal else None,
    )


@blueprint.route("/<int:id>/edit/")
@login_required
async def update(id: int):
    user = await current_user.get_user()
    event = await actions.event.get(user, id=id)

    if not actions.event.has_permission(user, event, enums.Permission.UPDATE):
        raise Forbidden()

    modal = 1 if "modal" in request.args else None

    return await render_template(
        "event/update.html",
        event=event,
        status_options=[(x.value.title(), x.value) for x in enums.EventStatus],
        r=url_for(".view", id=event.id),
        tab="event",
        base_template="modal_base.html" if modal else None,
    )


@blueprint.websocket("/<int:id>/ws")
async def ws(id: int) -> None:
    user = await current_user.get_user()
    event = await actions.event.get(user, id=id)

    if not actions.event.has_permission(user, event, enums.Permission.READ):
        raise Forbidden()

    async with MessageManager(
        user,
        f"event-{id}",
        session_id=websocket.args.get("SESSION_ID"),
    ) as mm:
        while True:
            data = await websocket.receive()
            await mm.send_message("message", data)
