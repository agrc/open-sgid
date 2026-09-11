"""
__init__.py
A module that denotes this as a module
"""

import logging
from os import getenv
from sys import stdout

import psycopg2
from google.cloud.logging.handlers import StructuredLogHandler

logger = logging.getLogger(__name__)

CONNECTION_TABLE_CACHE = {}

level = getenv("LOG_LEVEL", "INFO")
log_level = logging.INFO

if level == "DEBUG":
    log_level = logging.DEBUG
elif level == "INFO":
    log_level = logging.INFO
elif level == "WARNING":
    log_level = logging.WARNING
elif level == "ERROR":
    log_level = logging.ERROR
elif level == "CRITICAL":
    log_level = logging.CRITICAL

stream_handler = StructuredLogHandler(stream=stdout)
logging.basicConfig(handlers=[stream_handler], level=log_level)


def execute_sql(sql, connection):
    """executes sql on the information
    sql: string T-SQL
    connection: dict with connection information
    """
    logger.debug("  executing %s", sql)

    with psycopg2.connect(**connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)

        conn.commit()
