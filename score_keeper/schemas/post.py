from datetime import datetime
from typing import List, Optional, Union

from pydantic import StringConstraints, field_validator
from typing_extensions import Annotated

from score_keeper import enums

from .helpers import NOTSET, BaseModel, parse_list, remove_queryset
from .pagination import PageInfo, Pagination
from .query import Query
from .user import UserPublic

TITLE_VALIDATOR = Annotated[str, StringConstraints(min_length=5)]
CONTENT_VALIDATOR = str
STATUS_VALIDATOR = enums.PostStatus


class PostCreate(BaseModel):
    title: TITLE_VALIDATOR
    content: CONTENT_VALIDATOR
    status: STATUS_VALIDATOR = enums.PostStatus.DRAFT


class PostPatch(BaseModel):
    title: TITLE_VALIDATOR = NOTSET
    content: CONTENT_VALIDATOR = NOTSET
    status: STATUS_VALIDATOR = NOTSET


class Post(BaseModel):
    id: int
    title: str
    content: str
    status: str
    created_at: datetime
    modified_at: datetime
    published_at: Optional[datetime]
    viewed: int

    author_id: int
    author: Optional[UserPublic]

    _remove_queryset = field_validator("author", mode="before")(remove_queryset)


class PostFilterField(enums.EnumStr):
    ID_IN = "id__in"
    STATUS = "_status"
    AUTHOR_ID = "author_id"


class PostFilter(BaseModel):
    field: PostFilterField
    value: Union[str, int, List[str], List[int]]


class PostSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    TITLE_ASC = "title"
    TITLE_DESC = "-title"
    CREATED_AT_ASC = "created_at"
    CREATED_AT_DESC = "-created_at"
    PUBLISHED_AT_ASC = "published_at"
    PUBLISHED_AT_DESC = "-published_at"


class PostResolve(enums.EnumStr):
    AUTHOR = "author"


class PostGetOptions(BaseModel):
    resolves: Optional[List[PostResolve]] = []

    _parse_list = field_validator("resolves", mode="before")(parse_list)


class PostQuery(BaseModel, Query):
    filters: List[PostFilter] = []
    sorts: List[PostSort] = [PostSort.ID_ASC]
    resolves: Optional[List[PostResolve]] = []


class PostQueryStringSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    TITLE_ASC = "title__id"
    TITLE_DESC = "-title__id"
    CREATED_AT_ASC = "created_at__id"
    CREATED_AT_DESC = "-created_at__-id"
    PUBLISHED_AT_ASC = "published_at__created_at__id"
    PUBLISHED_AT_DESC = "-published_at__-created_at__-id"


class PostQueryString(BaseModel):
    sort: Optional[PostQueryStringSort] = PostQueryStringSort.PUBLISHED_AT_DESC
    id__in: Optional[List[int]] = None
    status: Optional[enums.PostStatus] = None
    author_id: Optional[int] = None
    pp: Optional[int] = 10
    p: Optional[int] = 1
    resolves: Optional[List[PostResolve]] = []

    _parse_list = field_validator("id__in", "resolves", mode="before")(parse_list)

    def to_query(self, resolves=None):
        filters = []
        if self.id__in:
            filters.append(PostFilter(field=PostFilterField.ID_IN, value=self.id__in))

        if self.status:
            filters.append(PostFilter(field=PostFilterField.STATUS, value=self.status))

        if self.author_id:
            filters.append(
                PostFilter(field=PostFilterField.AUTHOR_ID, value=self.author_id)
            )

        resolves = resolves or self.resolves
        sorts = self.sort.split("__")
        page_info = PageInfo(num_per_page=self.pp, current_page=self.p)
        return PostQuery(
            filters=filters, sorts=sorts, resolves=resolves, page_info=page_info
        )


class PostResultSet(BaseModel):
    pagination: Pagination
    posts: List[Post]


class PostLike(BaseModel):
    id: int

    post_id: int
    post: Optional[Post]

    user_id: int
    user: Optional[UserPublic]

    _remove_queryset = field_validator("post", "user", mode="before")(remove_queryset)
