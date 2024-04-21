from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "event" ADD "away_team_id" INT;
        ALTER TABLE "event" ADD "home_score" INT NOT NULL  DEFAULT 0;
        ALTER TABLE "event" ADD "home_team_id" INT;
        ALTER TABLE "event" ADD "away_score" INT NOT NULL  DEFAULT 0;
        DROP TABLE IF EXISTS "competitor";
        ALTER TABLE "event" ADD CONSTRAINT "fk_event_team_750e3531" FOREIGN KEY ("home_team_id") REFERENCES "team" ("id") ON DELETE CASCADE;
        ALTER TABLE "event" ADD CONSTRAINT "fk_event_team_d421adf2" FOREIGN KEY ("away_team_id") REFERENCES "team" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "event" DROP CONSTRAINT "fk_event_team_d421adf2";
        ALTER TABLE "event" DROP CONSTRAINT "fk_event_team_750e3531";
        ALTER TABLE "event" DROP COLUMN "away_team_id";
        ALTER TABLE "event" DROP COLUMN "home_score";
        ALTER TABLE "event" DROP COLUMN "home_team_id";
        ALTER TABLE "event" DROP COLUMN "away_score";"""
