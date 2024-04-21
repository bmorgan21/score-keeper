from datetime import datetime
from typing import List, Optional, Union

from pydantic import field_validator

from score_keeper import enums

from .helpers import (
    NOTSET,
    BaseModel,
    parse_list,
    remove_queryset,
    remove_reverse_relation,
)
from .pagination import PageInfo, Pagination
from .query import Query
from .team import Team
from .user import UserPublic

HOME_AWAY_VALIDATOR = enums.HomeAway
PERIOD_VALIDATOR = int
SCORE_VALIDATOR = int
SEASON_VALIDATOR = int
STATUS_VALIDATOR = enums.EventStatus


class CompetitorCreate(BaseModel):
    home_away: HOME_AWAY_VALIDATOR
    team_id: int = None


class CompetitorPatch(BaseModel):
    home_away: HOME_AWAY_VALIDATOR = NOTSET
    score: SCORE_VALIDATOR = NOTSET
    team_id: int = NOTSET


class Competitor(BaseModel):
    id: int
    home_away: str
    score: int
    created_at: datetime
    modified_at: datetime

    event_id: int
    team_id: Optional[int]
    team: Optional[Team]

    _remove_queryset = field_validator("team", mode="before")(remove_queryset)


class EventCreate(BaseModel):
    season: SEASON_VALIDATOR


class EventPatch(BaseModel):
    period: PERIOD_VALIDATOR = NOTSET
    season: SEASON_VALIDATOR = NOTSET
    status: STATUS_VALIDATOR = NOTSET


class Event(BaseModel):
    id: int
    period: int
    season: int
    status: str
    status_as_of: datetime
    created_at: datetime
    modified_at: datetime

    created_by_id: int
    created_by: Optional[UserPublic]

    competitors: Optional[List[Competitor]]

    _remove_queryset = field_validator("created_by", mode="before")(remove_queryset)
    _remove_reverse_relation = field_validator("competitors", mode="before")(
        remove_reverse_relation
    )


class EventFilterField(enums.EnumStr):
    ID_IN = "id__in"
    STATUS = "_status"


class EventFilter(BaseModel):
    field: EventFilterField
    value: Union[str, int, List[str], List[int]]


class EventSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    CREATED_AT_ASC = "created_at"
    CREATED_AT_DESC = "-created_at"
    MODIFIED_AT_ASC = "modified_at"
    MODIFIED_AT_DESC = "-modified_at"


class EventResolve(enums.EnumStr):
    CREATED_BY = "created_by"
    COMPETITORS = "competitors"
    COMPETITORS_TEAM = "competitors__team"


class EventGetOptions(BaseModel):
    resolves: Optional[List[EventResolve]] = []

    _parse_list = field_validator("resolves", mode="before")(parse_list)


class EventQuery(BaseModel, Query):
    filters: List[EventFilter] = []
    sorts: List[EventSort] = [EventSort.ID_ASC]
    resolves: Optional[List[EventResolve]] = []


class EventQueryStringSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    CREATED_AT_ASC = "created_at__id"
    CREATED_AT_DESC = "-created_at__-id"
    MODIFIED_AT_ASC = "modified_at__created_at__id"
    MODIFIED_AT_DESC = "-modified_at__-created_at__-id"


class EventQueryString(BaseModel):
    sort: Optional[EventQueryStringSort] = EventQueryStringSort.MODIFIED_AT_DESC
    id__in: Optional[List[int]] = None
    status: Optional[enums.EventStatus] = None
    pp: Optional[int] = 10
    p: Optional[int] = 1
    resolves: Optional[List[EventResolve]] = []

    _parse_list = field_validator("id__in", "resolves", mode="before")(parse_list)

    def to_query(self, resolves=None):
        filters = []
        if self.id__in:
            filters.append(EventFilter(field=EventFilterField.ID_IN, value=self.id__in))

        if self.status:
            filters.append(
                EventFilter(field=EventFilterField.STATUS, value=self.status)
            )

        resolves = resolves or self.resolves
        sorts = self.sort.split("__")
        page_info = PageInfo(num_per_page=self.pp, current_page=self.p)
        return EventQuery(
            filters=filters, sorts=sorts, resolves=resolves, page_info=page_info
        )


class EventResultSet(BaseModel):
    pagination: Pagination
    events: List[Event]
