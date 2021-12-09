#!/usr/bin/env python
# * coding: utf8 *
"""
__init__.py
A module that denotes this as a module
"""

import psycopg2

from .logger import Logger

LOG = Logger()
CONNECTION_TABLE_CACHE = {}


def execute_sql(sql, connection):
    """executes sql on the information
    sql: string T-SQL
    connection: dict with connection information
    """
    LOG.debug(f'  executing {sql}')

    with psycopg2.connect(**connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)

        conn.commit()
