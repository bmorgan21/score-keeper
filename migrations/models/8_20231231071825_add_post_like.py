from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "post" ALTER COLUMN "status" SET DEFAULT 'draft';
        ALTER TABLE "post" ALTER COLUMN "status" TYPE VARCHAR(16) USING "status"::VARCHAR(16);
        CREATE TABLE IF NOT EXISTS "postlike" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "post_id" INT NOT NULL REFERENCES "post" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_postlike_post_id_f233ef" UNIQUE ("post_id", "user_id")
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "post" ALTER COLUMN "status" SET DEFAULT 'pending';
        ALTER TABLE "post" ALTER COLUMN "status" TYPE VARCHAR(16) USING "status"::VARCHAR(16);
        DROP TABLE IF EXISTS "postlike";"""
