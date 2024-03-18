import asyncio
import json

from quart import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
    websocket,
)
from quart_auth import current_user, login_required

from score_keeper import actions, enums, schemas
from score_keeper.lib.auth import Forbidden
from score_keeper.lib.message_manager import MessageManager

blueprint = Blueprint("chat", __name__, template_folder="templates")


@blueprint.get("")
async def index():
    # needed so that the session cookie will be set correctly for logged out users
    await current_user.get_user()

    return await render_template("chat/index.html", tab="chat")


@blueprint.websocket("/ws")
async def ws() -> None:
    user = await current_user.get_user()

    async with MessageManager(
        user,
        "channel",
        session_id=websocket.args.get("SESSION_ID"),
    ) as mm:
        while True:
            message = await websocket.receive()
            await mm.send_message(
                "message",
                message,
                data=json.loads(schemas.UserPublic.model_dump_json(user)),
            )
