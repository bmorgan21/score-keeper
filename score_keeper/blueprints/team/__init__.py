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

blueprint = Blueprint("team", __name__, template_folder="templates")


@blueprint.route("/")
@validate_querystring(schemas.TeamQueryString)
async def index(query_args: schemas.TeamQueryString):
    user = await current_user.get_user()
    resultset = await actions.team.query(
        user, query_args.to_query(resolves=["created_by"])
    )

    can_edit = {}
    for team in resultset.teams:
        can_edit[team.id] = actions.team.has_permission(
            user, team, enums.Permission.UPDATE
        )

    return await render_template(
        "team/index.html", resultset=resultset, tab="team", can_edit=can_edit
    )


@blueprint.route("/create/")
@login_required
async def create():
    user = await current_user.get_user()
    if not actions.team.has_permission(user, None, enums.Permission.CREATE):
        raise Forbidden()

    now = datetime.datetime.now(datetime.UTC)

    team = schemas.Object()
    team.id = 0
    team.season = now.year

    modal = 1 if "modal" in request.args else None

    return await render_template(
        "team/create.html",
        r=url_for(".index", author_id=user.id),
        tab="team",
        team=team,
        base_template="modal_base.html" if modal else None,
    )


@blueprint.route("/<int:id>/edit/")
@login_required
async def update(id: int):
    user = await current_user.get_user()
    team = await actions.team.get(user, id=id)

    if not actions.team.has_permission(user, team, enums.Permission.UPDATE):
        raise Forbidden()

    modal = 1 if "modal" in request.args else None

    return await render_template(
        "team/create.html",
        team=team,
        r=url_for(".index"),
        tab="team",
        base_template="modal_base.html" if modal else None,
    )
