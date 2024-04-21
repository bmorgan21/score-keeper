from datetime import datetime
from typing import List, Optional, Union

from pydantic import field_validator

from score_keeper import enums

from .helpers import NOTSET, BaseModel, parse_list, remove_queryset
from .pagination import PageInfo, Pagination
from .query import Query
from .user import UserPublic


class TeamCreate(BaseModel):
    name: str


class TeamPatch(BaseModel):
    name: str = NOTSET


class Team(BaseModel):
    id: int
    name: str
    created_at: datetime
    modified_at: datetime

    created_by_id: int
    created_by: Optional[UserPublic]

    _remove_queryset = field_validator("created_by", mode="before")(remove_queryset)


class TeamFilterField(enums.EnumStr):
    ID_IN = "id__in"


class TeamFilter(BaseModel):
    field: TeamFilterField
    value: Union[str, int, List[str], List[int]]


class TeamSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    CREATED_AT_ASC = "created_at"
    CREATED_AT_DESC = "-created_at"
    MODIFIED_AT_ASC = "modified_at"
    MODIFIED_AT_DESC = "-modified_at"


class TeamResolve(enums.EnumStr):
    CREATED_BY = "created_by"


class TeamGetOptions(BaseModel):
    resolves: Optional[List[TeamResolve]] = []

    _parse_list = field_validator("resolves", mode="before")(parse_list)


class TeamQuery(BaseModel, Query):
    filters: List[TeamFilter] = []
    sorts: List[TeamSort] = [TeamSort.ID_ASC]
    resolves: Optional[List[TeamResolve]] = []


class TeamQueryStringSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    CREATED_AT_ASC = "created_at__id"
    CREATED_AT_DESC = "-created_at__-id"
    MODIFIED_AT_ASC = "modified_at__created_at__id"
    MODIFIED_AT_DESC = "-modified_at__-created_at__-id"


class TeamQueryString(BaseModel):
    sort: Optional[TeamQueryStringSort] = TeamQueryStringSort.MODIFIED_AT_DESC
    id__in: Optional[List[int]] = None
    pp: Optional[int] = 10
    p: Optional[int] = 1
    resolves: Optional[List[TeamResolve]] = []

    _parse_list = field_validator("id__in", "resolves", mode="before")(parse_list)

    def to_query(self, resolves=None):
        filters = []
        if self.id__in:
            filters.append(TeamFilter(field=TeamFilterField.ID_IN, value=self.id__in))

        resolves = resolves or self.resolves
        sorts = self.sort.split("__")
        page_info = PageInfo(num_per_page=self.pp, current_page=self.p)
        return TeamQuery(
            filters=filters, sorts=sorts, resolves=resolves, page_info=page_info
        )


class TeamResultSet(BaseModel):
    pagination: Pagination
    teams: List[Team]
