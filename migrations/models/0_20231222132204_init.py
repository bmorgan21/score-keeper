from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "auth_id" VARCHAR(64)  UNIQUE,
    "email" VARCHAR(128) NOT NULL UNIQUE,
    "hashed_password" BYTEA,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'active',
    "name" VARCHAR(32),
    "picture" TEXT,
    "role" VARCHAR(16) NOT NULL  DEFAULT 'user'
);
COMMENT ON COLUMN "user"."role" IS 'ADMIN: admin\nUSER: user';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
