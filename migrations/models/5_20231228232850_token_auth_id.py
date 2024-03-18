from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP CONSTRAINT "user_auth_id_key";
        CREATE TABLE IF NOT EXISTS "token" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "type" VARCHAR(20) NOT NULL  DEFAULT 'web',
    "name" VARCHAR(32) NOT NULL,
    "auth_id" VARCHAR(64) NOT NULL UNIQUE,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "token"."type" IS 'WEB: web\nAPI: api';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "token";
        CREATE UNIQUE INDEX "uid_user_auth_id_a6b8fa" ON "user" ("auth_id");"""
