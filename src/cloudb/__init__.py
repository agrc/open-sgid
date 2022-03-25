#!/usr/bin/env python
# * coding: utf8 *
"""
__init__.py
A module that denotes this as a module
"""

import logging
from sys import stdout

import psycopg2

CONNECTION_TABLE_CACHE = {}

logging.basicConfig(
    stream=stdout,
    format='%(levelname)-7s %(asctime)s %(module)10s:%(lineno)5s %(message)s',
    datefmt='%m-%d %H:%M:%S',
    level=logging.DEBUG
)

def execute_sql(sql, connection):
    """executes sql on the information
    sql: string T-SQL
    connection: dict with connection information
    """
    logging.debug('  executing %s', sql)

    with psycopg2.connect(**connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)

        conn.commit()
