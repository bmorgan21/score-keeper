import hashlib
from typing import List, Optional, Union

from pydantic import HttpUrl, field_validator
from unique_names_generator import get_random_name
from unique_names_generator.data import ADJECTIVES, ANIMALS

from score_keeper import enums

from .helpers import NOTSET, BaseModel, EmailStr, PasswordStr, parse_list
from .pagination import PageInfo, Pagination
from .query import Query

ROLE_VALIDATOR = enums.UserRole
NAME_VALIDATOR = str
EMAIL_VALIDATOR = EmailStr
STATUS_VALIDATOR = enums.UserStatus
PICTURE_VALIDATOR = HttpUrl
PASSWORD_VALIDATOR = PasswordStr


class UserCreate(BaseModel):
    name: NAME_VALIDATOR
    email: EMAIL_VALIDATOR
    picture: Optional[PICTURE_VALIDATOR] = None
    password: Optional[PASSWORD_VALIDATOR] = None


class UserPatch(BaseModel):
    name: NAME_VALIDATOR = NOTSET
    email: EMAIL_VALIDATOR = NOTSET
    # Optional means the value can be None
    # https://docs.pydantic.dev/2.0/migration/#required-optional-and-nullable-fields
    picture: Optional[PICTURE_VALIDATOR] = NOTSET


class UserPublic(BaseModel):
    id: int
    name: str
    picture: Optional[PICTURE_VALIDATOR]


class User(BaseModel):
    id: int
    role: str
    name: str
    email: str
    status: str
    picture: Optional[PICTURE_VALIDATOR]

    @classmethod
    def system_user(cls):
        email = "system@example.com"

        return cls(
            id=0,
            auth_id=None,
            name="System User",
            role=enums.UserRole.ADMIN,
            email=email,
            status=enums.UserStatus.ACTIVE,
            picture=cls.get_gravatar(email),
        )

    @classmethod
    def anonymous_user(cls):
        name = get_random_name(combo=[ADJECTIVES, ANIMALS], style="lowercase")
        email = name.replace(" ", ".") + "@gmail.com"

        return cls(
            id=0,
            auth_id=None,
            name=name,
            role=enums.UserRole.USER,
            email=email,
            status=enums.UserStatus.PENDING,
            picture=cls.get_gravatar(email),
        )

    @classmethod
    def get_gravatar(cls, email):
        md5_hash = hashlib.md5(email.encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{md5_hash}?s=100&d=identicon"


class UserFilterField(enums.EnumStr):
    ID_IN = "id__in"


class UserFilter(BaseModel):
    field: UserFilterField
    value: Union[str, int, List[str], List[int]]


class UserSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    EMAIL_ASC = "email"
    EMAIL_DESC = "-email"
    NAME_ASC = "name"
    NAME_DESC = "-name"


class UserResolve(enums.EnumStr):
    pass


class UserGetOptions(BaseModel):
    resolves: Optional[List[UserResolve]] = []

    _parse_list = field_validator("resolves", mode="before")(parse_list)


class UserQuery(BaseModel, Query):
    filters: List[UserFilter] = []
    sorts: List[UserSort] = [UserSort.ID_ASC]
    resolves: Optional[List[UserResolve]] = []


class UserQueryStringSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    EMAIL_ASC = "email__id"
    EMAIL_DESC = "-email__id"
    NAME_ASC = "name__id"
    NAME_DESC = "-name__id"


class UserQueryString(BaseModel):
    sort: Optional[UserQueryStringSort] = UserQueryStringSort.ID_ASC
    id__in: Optional[List[int]] = None
    pp: Optional[int] = 10
    p: Optional[int] = 1
    resolves: Optional[List[UserResolve]] = []

    _parse_list = field_validator("id__in", "resolves", mode="before")(parse_list)

    def to_query(self, resolves=None):
        filters = []
        if self.id__in:
            filters.append(UserFilter(field=UserFilterField.ID_IN, value=self.id__in))

        resolves = resolves or self.resolves
        sorts = self.sort.split("__")
        page_info = PageInfo(num_per_page=self.pp, current_page=self.p)
        return UserQuery(
            filters=filters, sorts=sorts, resolves=resolves, page_info=page_info
        )


class UserResultSet(BaseModel):
    pagination: Pagination
    users: List[User]
