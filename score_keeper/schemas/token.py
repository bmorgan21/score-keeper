from typing import List, Optional, Union

from pydantic import StringConstraints, field_validator
from typing_extensions import Annotated

from score_keeper import enums

from .helpers import BaseModel, parse_list, remove_queryset
from .pagination import PageInfo, Pagination
from .query import Query
from .user import UserPublic

TYPE_VALIDATOR = enums.TokenType
NAME_VALIDATOR = Annotated[str, StringConstraints(min_length=1, max_length=32)]


class TokenCreate(BaseModel):
    name: NAME_VALIDATOR


class TokenCreateSuccess(BaseModel):
    id: int
    type: str
    name: str
    auth_id: str
    user_id: int


class TokenPatch(BaseModel):
    name: NAME_VALIDATOR


class Token(BaseModel):
    id: int
    type: str
    name: str
    user_id: int
    user: Optional[UserPublic]

    _remove_queryset = field_validator("user", mode="before")(remove_queryset)


class TokenFilterField(enums.EnumStr):
    ID_IN = "id__in"


class TokenFilter(BaseModel):
    field: TokenFilterField
    value: Union[str, int, List[str], List[int]]


class TokenSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"


class TokenResolve(enums.EnumStr):
    USER = "user"


class TokenGetOptions(BaseModel):
    resolves: Optional[List[TokenResolve]] = []

    _parse_list = field_validator("resolves", mode="before")(parse_list)


class TokenQuery(BaseModel, Query):
    filters: List[TokenFilter] = []
    sorts: List[TokenSort] = [TokenSort.ID_ASC]
    resolves: Optional[List[TokenResolve]] = []


class TokenQueryStringSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"


class TokenQueryString(BaseModel):
    sort: Optional[TokenQueryStringSort] = TokenQueryStringSort.ID_ASC
    id__in: Optional[List[int]] = None
    pp: Optional[int] = 10
    p: Optional[int] = 1
    resolves: Optional[List[TokenResolve]] = []

    _parse_list = field_validator("id__in", "resolves", mode="before")(parse_list)

    def to_query(self, resolves=None):
        filters = []
        if self.id__in:
            filters.append(TokenFilter(field=TokenFilterField.ID_IN, value=self.id__in))

        resolves = resolves or self.resolves
        sorts = self.sort.split("__")
        page_info = PageInfo(num_per_page=self.pp, current_page=self.p)
        return TokenQuery(
            filters=filters, sorts=sorts, resolves=resolves, page_info=page_info
        )


class TokenResultSet(BaseModel):
    pagination: Pagination
    tokens: List[Token]
