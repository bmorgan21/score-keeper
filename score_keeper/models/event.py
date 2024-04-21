import datetime as dt

from tortoise import Model, fields

from score_keeper import enums

from .helpers import TimestampMixin
from .team import Team
from .user import User


class Event(TimestampMixin, Model):
    id = fields.IntField(pk=True)
    _status = fields.CharEnumField(
        enums.EventStatus,
        max_length=16,
        default=enums.EventStatus.NOT_STARTED,
        source_field="status",
    )
    season = fields.IntField()
    period = fields.IntField(default=1)
    status_as_of = fields.DatetimeField(auto_now_add=True)

    created_by: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="events"
    )

    @property
    def status(self):
        return self._status

    def update_status(self, status):
        if status != self._status:
            self._status = status
            self.status_as_of = dt.datetime.now(dt.timezone.utc)


class Competitor(TimestampMixin, Model):
    id = fields.IntField(pk=True)
    score = fields.IntField(default=0)
    home_away = fields.CharEnumField(enums.HomeAway, max_length=16)

    event: fields.ForeignKeyRelation[Event] = fields.ForeignKeyField(
        "models.Event", related_name="competitors"
    )
    team: fields.ForeignKeyRelation[Team] = fields.ForeignKeyField(
        "models.Team", null=True
    )

    class Meta:
        unique_together = ("event_id", "home_away")
