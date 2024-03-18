import logging
import sys

fmt = logging.Formatter(
    fmt="[%(asctime)s] %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
sh.setFormatter(fmt)


def register_logging(app):
    debug_query = app.config["TORTOISE_ORM_DEBUG_QUERY"]
    if (debug_query is None and app.debug) or (debug_query is not None and debug_query):
        # will print debug sql
        logger_db_client = logging.getLogger("tortoise.db_client")
        logger_db_client.setLevel(logging.DEBUG)
        logger_db_client.addHandler(sh)
