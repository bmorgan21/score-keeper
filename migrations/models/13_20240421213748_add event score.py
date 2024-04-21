from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "eventscore" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "away_delta" INT NOT NULL  DEFAULT 0,
    "home_delta" INT NOT NULL  DEFAULT 0,
    "away_score" INT NOT NULL,
    "home_score" INT NOT NULL,
    "comment" TEXT,
    "event_id" INT NOT NULL REFERENCES "event" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "eventscore";"""
