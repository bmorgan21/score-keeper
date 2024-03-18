import asyncio
import json
import uuid
from typing import Any

from quart import Blueprint, current_app, redirect, url_for, websocket
from quart.templating import render_template
from quart_auth import current_user, login_required
from quart_schema import validate_querystring

from score_keeper import actions, enums, schemas
from score_keeper.lib.auth import Forbidden
from score_keeper.lib.error import ActionError
from score_keeper.lib.message_manager import MessageManager

blueprint = Blueprint("post", __name__, template_folder="templates")


@blueprint.route("/")
@validate_querystring(schemas.PostQueryString)
async def index(query_args: schemas.PostQueryString):
    if not query_args.status:
        return redirect(url_for(".index", status=enums.PostStatus.PUBLISHED))
    user = await current_user.get_user()
    resultset = await actions.post.query(user, query_args.to_query(resolves=["author"]))

    subtab = query_args.status
    if query_args.author_id == user.id:
        subtab = f"mine-{subtab}"

    return await render_template(
        "post/index.html", resultset=resultset, tab="blog", subtab=subtab
    )


@blueprint.route("/<int:id>")
async def view(id: int):
    user = await current_user.get_user()
    post = await actions.post.get(
        user, id=id, options=schemas.PostGetOptions(resolves=["author"])
    )

    try:
        post_like = await actions.post.get_like(user, id)
    except ActionError as error:
        if error.type != "action_error.does_not_exist":
            raise
        post_like = None

    await actions.post.view(user, id)
    post.viewed += 1  # make sure the user sees their view

    mm = MessageManager(user, f"post-{id}")
    await mm.send_message("view", f"User {user.id} viewed page", post.viewed)

    can_edit = actions.post.has_permission(user, post, enums.Permission.UPDATE)

    return await render_template(
        "post/view.html", post=post, post_like=post_like, can_edit=can_edit
    )


@blueprint.route("/create/")
@login_required
async def create():
    user = await current_user.get_user()
    if not actions.post.has_permission(user, None, enums.Permission.CREATE):
        raise Forbidden()

    return await render_template(
        "post/create.html",
        status_options=[(x.value.title(), x.value) for x in enums.PostStatus],
        r=url_for(".index", status="{-status-}", author_id=user.id),
        tab="blog",
    )


@blueprint.route("/<int:id>/edit/")
@login_required
async def update(id: int):
    user = await current_user.get_user()
    post = await actions.post.get(user, id=id)

    if not actions.post.has_permission(user, post, enums.Permission.UPDATE):
        raise Forbidden()

    return await render_template(
        "post/create.html",
        post=post,
        status_options=[(x.value.title(), x.value) for x in enums.PostStatus],
        r=url_for(".view", id=post.id),
        tab="blog",
    )


@blueprint.websocket("/<int:id>/ws")
async def ws(id: int) -> None:
    user = await current_user.get_user()
    post = await actions.post.get(user, id=id)

    if not actions.post.has_permission(user, post, enums.Permission.READ):
        raise Forbidden()

    async with MessageManager(
        user,
        f"post-{id}",
        session_id=websocket.args.get("SESSION_ID"),
    ) as mm:
        while True:
            data = await websocket.receive()
            await mm.send_message("message", data)
