from tortoise import Model, fields

from score_keeper import enums

from .helpers import TimestampMixin
from .user import User


class Token(TimestampMixin, Model):
    id = fields.IntField(pk=True)
    type = fields.CharEnumField(
        enums.TokenType, max_length=20, default=enums.TokenType.WEB
    )
    name = fields.CharField(32)
    auth_id = fields.CharField(64, unique=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="tokens"
    )
