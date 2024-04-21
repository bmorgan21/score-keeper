from tortoise import Model, fields

from .helpers import TimestampMixin
from .user import User


class Team(TimestampMixin, Model):
    name = fields.CharField(128)

    created_by: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="teams_created"
    )
