from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "event" ADD "datetime" TIMESTAMPTZ;
        ALTER TABLE "event" DROP COLUMN "date";
        ALTER TABLE "event" DROP COLUMN "time";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "event" ADD "date" DATE;
        ALTER TABLE "event" ADD "time" TIMETZ;
        ALTER TABLE "event" DROP COLUMN "datetime";"""
