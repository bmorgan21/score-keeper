from typing import Union, get_args, get_origin

from pydantic import AfterValidator
from pydantic import BaseModel as PydanticBaseModel
from pydantic import EmailStr as PydanticEmailStr
from pydantic import ValidationInfo, field_validator
from pydantic_core import PydanticCustomError
from tortoise.queryset import QuerySet
from typing_extensions import Annotated


def PydanticValueError(msg, type=None):
    return PydanticCustomError(f"value_error.{type}" if type else "value_error", msg)


def remove_queryset(value: str):
    return None if isinstance(value, QuerySet) else value


def parse_list(value: str):
    return value.split(",") if isinstance(value, str) else value


def validate_password(value: str):
    if len(value) < 8:
        raise PydanticValueError(
            "Password must be at least 8 characters long.", type="password"
        )

    if len(value) > 16:
        raise PydanticValueError(
            "Password must not be greater than 16 characters long.", type="password"
        )

    if not any(char.isupper() for char in value):
        raise PydanticValueError(
            "Password must contain at least one uppercase letter", type="password"
        )

    if not any(char.islower() for char in value):
        raise PydanticValueError(
            "Password must contain at least one lowercase letter", type="password"
        )

    if not any(char.isdigit() for char in value):
        raise PydanticValueError(
            "Password must contain at least one digit", type="password"
        )

    return value


def is_optional(field):
    return get_origin(field) is Union and type(None) in get_args(field)


class BaseModel(PydanticBaseModel):
    class Config:
        from_attributes = True

    @field_validator("*", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: str, info: ValidationInfo):
        """
        For all fields that can be None (i.e. Optional[...]), convert empty strings to None

        For all fields that can not be None and are an empty string raise a Field Required
        error before the standard validation can run.
        """
        field = cls.model_fields[info.field_name]

        if is_optional(field.annotation):
            if value == "":
                return None
        elif value == "":
            raise PydanticValueError("Field is Required")
        return value


NOTSET = object()


PasswordStr = Annotated[str, AfterValidator(validate_password)]
EmailStr = PydanticEmailStr
