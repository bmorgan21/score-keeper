from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "team" ADD "created_by_id" INT NOT NULL;
        ALTER TABLE "team" ADD CONSTRAINT "fk_team_user_5c7cdce2" FOREIGN KEY ("created_by_id") REFERENCES "user" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "team" DROP CONSTRAINT "fk_team_user_5c7cdce2";
        ALTER TABLE "team" DROP COLUMN "created_by_id";"""
