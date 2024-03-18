import json
from functools import wraps
from typing import Any, Callable

from quart import current_app, session
from quart_auth import AuthUser as _AuthUser
from quart_auth import Unauthorized, current_user

from score_keeper import actions, schemas

from .error import ActionError

ANONYMOUS_USER = "anonymous_user"


class Forbidden(Exception):
    pass


class AuthUser(_AuthUser):
    def __init__(self, auth_id):
        super().__init__(auth_id)
        self._resolved = False
        self._user = None
        self._token = None

    async def _resolve(self):
        if not self._resolved:
            system_user = schemas.User.system_user()
            try:
                self._token = await actions.token.get(system_user, auth_id=self.auth_id)
                self._user = await actions.user.get(system_user, id=self._token.user_id)
                session.pop(ANONYMOUS_USER, None)
            except ActionError as error:
                if error.type not in ("action_error.not_found", "action_error.does_not_exist"):
                    raise

                try:
                    self._user = schemas.User.model_validate(
                        json.loads(session[ANONYMOUS_USER])
                    )
                except (KeyError, json.decoder.JSONDecodeError):
                    self._user = schemas.User.anonymous_user()
                    session[ANONYMOUS_USER] = self._user.model_dump_json()

            self._resolved = True

    async def __getattr__(self, name):
        await self._resolve()
        if self._user:
            return getattr(self._user, name)
        return None

    @property
    async def is_authenticated(self) -> bool:
        return await super().is_authenticated and await self.id and await self.id > 0

    async def has_roles(self, roles):
        return await self.is_authenticated and await self.role in roles

    async def get_user(self):
        await self._resolve()
        return self._user

    async def get_token(self):
        await self._resolve()
        return self._token


def roles_accepted(*role_names) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        async def decorator(*args: Any, **kwargs: Any) -> Any:
            if not await current_user.is_authenticated:
                raise Unauthorized()

            if not await current_user.has_roles(role_names):
                raise Forbidden()

            return await current_app.ensure_async(func)(*args, **kwargs)

        return decorator

    return wrapper
