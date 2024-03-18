from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "status" TYPE VARCHAR(20) USING "status"::VARCHAR(20);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "status" TYPE VARCHAR(20) USING "status"::VARCHAR(20);"""
