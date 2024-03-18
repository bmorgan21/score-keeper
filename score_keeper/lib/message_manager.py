import asyncio
import json
from typing import Any, Optional
from uuid import uuid4

from quart import current_app, websocket

from score_keeper import schemas


class MessageManager:
    def __init__(
        self, user: schemas.User, channel_id: str, session_id: Optional[str] = None
    ):
        self.user = user
        self.channel_id = channel_id
        self.session_id = session_id or str(uuid4())

    async def __aenter__(self):
        await current_app.socket_manager.add_user_to_channel(
            self.channel_id, websocket._get_current_object()
        )

        await self.send_message(
            "connected",
            f"User {self.user.id} connected to channel - {self.channel_id}",
            data=json.loads(schemas.UserPublic.model_dump_json(self.user)),
        )

        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        if isinstance(exc_val, asyncio.CancelledError):
            await current_app.socket_manager.remove_user_from_channel(
                self.channel_id, websocket._get_current_object()
            )

            await self.send_message(
                "disconnected",
                f"User {self.user.id} disconnected from channel - {self.channel_id}",
                data=json.loads(schemas.UserPublic.model_dump_json(self.user)),
            )

    def __await__(self):
        return self.__aenter__().__await__()

    async def send_message(self, msg_type: str, message: str, data: Any = None):
        message = {
            "session_id": self.session_id,
            "user_id": self.user.id,
            "channel_id": self.channel_id,
            "message": message,
            "type": msg_type,
        }

        if data is not None:
            message["data"] = data

        await current_app.socket_manager.broadcast_to_channel(
            self.channel_id, json.dumps(message)
        )
