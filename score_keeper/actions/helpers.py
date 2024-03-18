import re
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Callable

from asyncpg.exceptions import UniqueViolationError
from tortoise.exceptions import DoesNotExist, IntegrityError

from score_keeper import schemas
from score_keeper.lib.error import ActionError

unique_violation_detail_re = re.compile(
    r"Key \((?P<columns>.*?)\)=\((?P<values>.*?)\) already exists."
)


def handle_orm_errors(func: Callable) -> Callable:
    def handle_does_not_exist(error):
        raise ActionError("Entity Not Found", type="does_not_exist") from error

    def handle_integrity_error(error):
        if isinstance(error.args[0], UniqueViolationError):
            m = unique_violation_detail_re.match(error.args[0].detail)

            if m:
                d = m.groupdict()
                raise ActionError(
                    f"{d['values']} already exists",
                    loc=[x.strip() for x in d["columns"].split(",")][0],
                    type="integrity",
                ) from error

        raise ActionError(str(error), type="integrity")

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DoesNotExist as error:
            handle_does_not_exist(error)
        except IntegrityError as error:
            handle_integrity_error(error)
        return None

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DoesNotExist as error:
            handle_does_not_exist(error)
        except IntegrityError as error:
            handle_integrity_error(error)
        return None

    return async_wrapper if iscoroutinefunction(func) else wrapper


def conditional_set(obj: Any, attr: str, value: Any) -> bool:
    if value != schemas.NOTSET:
        setattr(obj, attr, value)
