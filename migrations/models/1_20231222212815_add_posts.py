from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "post" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(128) NOT NULL,
    "status" VARCHAR(16) NOT NULL  DEFAULT 'pending',
    "content" TEXT NOT NULL,
    "author_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "post"."status" IS 'PENDING: pending\nPUBLISHED: published';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "post";"""
