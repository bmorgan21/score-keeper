from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "event" ADD "date" DATE;
        ALTER TABLE "event" ADD "time" TIMETZ;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "event" DROP COLUMN "date";
        ALTER TABLE "event" DROP COLUMN "time";"""
