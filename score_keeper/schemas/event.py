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

PERIOD_VALIDATOR = int
SCORE_VALIDATOR = int
SEASON_VALIDATOR = int
STATUS_VALIDATOR = enums.EventStatus


class EventScoreCreate(BaseModel):
    away_delta: int = NOTSET
    home_delta: int = NOTSET

    away_score: int
    home_score: int

    comment: str = NOTSET


class EventScore(BaseModel):
    id: int
    created_at: datetime
    modified_at: datetime

    away_delta: Optional[int]
    home_delta: Optional[int]

    away_score: int
    home_score: int

    comment: Optional[str]

    event_id: int


class EventCreate(BaseModel):
    season: SEASON_VALIDATOR
    away_team_id: Optional[int] = None
    home_team_id: Optional[int] = None


class EventPatch(BaseModel):
    period: PERIOD_VALIDATOR = NOTSET
    season: SEASON_VALIDATOR = NOTSET
    status: STATUS_VALIDATOR = NOTSET
    away_team_id: int = NOTSET
    away_score: SCORE_VALIDATOR = NOTSET
    home_team_id: int = NOTSET
    home_score: SCORE_VALIDATOR = NOTSET


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

    away_team_id: Optional[int]
    away_team: Optional[Team]
    away_score: int

    home_team_id: Optional[int]
    home_team: Optional[Team]
    home_score: int

    scores: Optional[List[EventScore]]

    _remove_queryset = field_validator(
        "created_by", "away_team", "home_team", mode="before"
    )(remove_queryset)

    _remove_reverse_relation = field_validator("scores", mode="before")(
        remove_reverse_relation
    )

    @property
    def away_team_name(self):
        return self.away_team.name if self.away_team else "Away"

    @property
    def home_team_name(self):
        return self.home_team.name if self.home_team else "Home"

    @property
    def verbose_status(self):
        if self.status == "not-started":
            return "Not Started"
        elif self.status == "in-progress":
            return "In Progress"
        elif self.status == "ended":
            return "Ended"
        return self.status


class EventFilterField(enums.EnumStr):
    ID_IN = "id__in"
    STATUS = "_status"
    CREATED_BY_ID = "created_by_id"


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
    AWAY_TEAM = "away_team"
    HOME_TEAM = "home_team"
    SCORES = "scores"


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
    created_by_id: Optional[int] = None
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
