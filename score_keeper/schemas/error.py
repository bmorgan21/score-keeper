from typing import Any, List, Optional

from .helpers import PydanticBaseModel


class Error(PydanticBaseModel):
    loc: str
    msg: str
    type: str
    input: Optional[Any] = None


class Errors(PydanticBaseModel):
    errors: List[Error]
