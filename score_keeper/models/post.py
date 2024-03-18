import datetime as dt

from tortoise import Model, fields

from score_keeper import enums

from .helpers import TimestampMixin
from .user import User


class Post(TimestampMixin, Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(128)
    _status = fields.CharEnumField(
        enums.PostStatus,
        max_length=16,
        default=enums.PostStatus.DRAFT,
        source_field="status",
    )
    content = fields.TextField()
    published_at = fields.DatetimeField(null=True)
    viewed = fields.IntField(default=0)

    author: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="documents"
    )

    @property
    def status(self):
        return self._status

    def update_status(self, status):
        if status != self._status:
            self._status = status
            if status == enums.PostStatus.PUBLISHED:
                self.published_at = dt.datetime.now(dt.timezone.utc)
            else:
                self.published_at = None


class PostLike(TimestampMixin, Model):
    id = fields.IntField(pk=True)

    post: fields.ForeignKeyRelation[Post] = fields.ForeignKeyField(
        "models.Post", related_name="likes"
    )
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="likes"
    )

    class Meta:
        unique_together = ("post_id", "user_id")
