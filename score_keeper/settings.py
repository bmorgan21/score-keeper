import os

from dotenv import load_dotenv


def strtobool(value):
    value_lower = "NONE" if value is None else value.lower()

    if value_lower in ("y", "yes", "true", "t", "1"):
        return True

    if value_lower in ("n", "no", "false", "f", "0"):
        return False

    return None


load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
UPLOADS_DEST = os.environ.get("UPLOADS_DEST", "tmp/uploads")

DB_ENGINE = os.environ.get("DB_ENGINE", "tortoise.backends.asyncpg")
DB_NAME = os.environ["DB_NAME"]
DB_HOST = os.environ["DB_HOST"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_USER = os.environ["DB_USER"]
DB_PORT = os.environ.get("DB_PORT", -1)

STATIC_VERSION = os.environ.get("STATIC_VERSION")

QUART_AUTH_COOKIE_SECURE = strtobool(os.environ.get("QUART_AUTH_COOKIE_SECURE", "True"))
QUART_SCHEMA_CONVERT_CASING = strtobool(
    os.environ.get("QUART_SCHEMA_CONVERT_CASING", "False")
)
AUTH_LOGIN_SUCCESS_ENDPOINT = os.environ.get(
    "AUTH_LOGIN_SUCCESS_ENDPOINT", "post.index"
)
AUTH_LOGOUT_SUCCESS_ENDPOINT = os.environ.get(
    "AUTH_LOGOUT_SUCCESS_ENDPOINT", "marketing.index"
)

TORTOISE_ORM_DEBUG_QUERY = False

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": DB_ENGINE,
            "credentials": {
                "database": DB_NAME,
                "host": DB_HOST,
                "password": DB_PASSWORD,
                "user": DB_USER,
                "port": DB_PORT,
            },
        }
    },
    "apps": {
        "models": {
            "models": ["score_keeper.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
