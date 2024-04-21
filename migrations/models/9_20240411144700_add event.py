from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "event" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "status" VARCHAR(16) NOT NULL  DEFAULT 'not-started',
    "season" INT NOT NULL,
    "period" INT NOT NULL  DEFAULT 1,
    "status_as_of" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "event"."status" IS 'NOT_STARTED: not-started\nIN_PROGRESS: in-progress\nENDED: ended';

        CREATE TABLE IF NOT EXISTS "team" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(128) NOT NULL
);
        CREATE TABLE IF NOT EXISTS "competitor" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "score" INT NOT NULL  DEFAULT 0,
    "home_away" VARCHAR(16) NOT NULL,
    "event_id" INT NOT NULL REFERENCES "event" ("id") ON DELETE CASCADE,
    "team_id" INT NOT NULL REFERENCES "team" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_competitor_event_i_a28d78" UNIQUE ("event_id", "home_away")
);
COMMENT ON COLUMN "competitor"."home_away" IS 'AWAY: away\nHOME: home';
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "competitor";
        DROP TABLE IF EXISTS "event";
        DROP TABLE IF EXISTS "team";"""
