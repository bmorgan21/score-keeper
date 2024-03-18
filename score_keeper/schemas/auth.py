from typing import Optional

from pydantic import ValidationInfo, field_validator

from .helpers import BaseModel, EmailStr, PasswordStr, PydanticValueError

EMAIL_VALIDATOR = EmailStr
PASSWORD_VALIDATOR = PasswordStr


class AuthTokenCreate(BaseModel):
    email: str
    password: str


class AuthUserCreate(BaseModel):
    email: EMAIL_VALIDATOR
    password: PASSWORD_VALIDATOR
    confirm_password: Optional[str]

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo):
        password = info.data.get("password")
        confirm_password = value

        if password is not None and password != confirm_password:
            raise PydanticValueError("Passwords do not match", type="password")

        return value
