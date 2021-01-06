#!/usr/bin/env python
# * coding: utf8 *
'''
schema.py
A module that modifies schemas
'''

from colorama import Back, Fore
import psycopg2
import pyodbc
from . import config, LOG


def drop_schemas(schemas):
    '''drops the schemas and all tables within
    schemas: array of schemas to create
    '''
    with psycopg2.connect(**config.DBO_CONNECTION) as conn:
        sql = []

        for name in schemas:
            sql.append(f'DROP SCHEMA {name} CASCADE')

        LOG.info(f'dropping schema for {sql}')
        with conn.cursor() as cursor:
            cursor.execute(';'.join(sql))

        conn.commit()


def create_schemas(schemas):
    '''creates the schemas to match our ISO categories
    schemas: array of schemas to create
    '''
    with psycopg2.connect(**config.DBO_CONNECTION) as conn:
        sql = []

        for name in schemas:
            sql.append(f'CREATE SCHEMA IF NOT EXISTS {name} AUTHORIZATION {config.ADMIN["name"]}')
            sql.append(f'GRANT ALL ON SCHEMA {name} TO {config.ADMIN["name"]}')
            sql.append(f'GRANT USAGE ON SCHEMA {name} TO public')

        LOG.info(f'creating schemas for {sql}')
        with conn.cursor() as cursor:
            cursor.execute(';'.join(sql))

        conn.commit()


def update_schema_for(sql_table, pg_table, dry_run=False):
    statements = []
    with pyodbc.connect(config.get_source_connection()[6:]) as conn:
        sql = """SELECT
    LOWER(column_name) as column_name, data_type
FROM
    INFORMATION_SCHEMA.COLUMNS
WHERE
    LOWER(table_name) = ?
    AND LOWER(table_schema) = ?
    AND data_type in ('smallint', 'int', 'bigint')
    AND column_name not in ('OBJECTID', 'OBJECTID_1');"""

        with conn.cursor() as cursor:
            schema_name, table_name = sql_table.split('.')
            result = cursor.execute(sql, table_name, schema_name)

            for column, data_type in result:
                statements.append(f'ALTER COLUMN {column} TYPE {data_type} USING {column}::{data_type}')

    import pdb; pdb.set_trace()
    with psycopg2.connect(**config.DBO_CONNECTION) as conn:
        with conn.cursor() as cursor:
            sql = f'ALTER TABLE {pg_table} {", ".join(statements)};'
            LOG.verbose(f'updating schema for {Fore.CYAN}{pg_table}{Fore.RESET} with {Fore.MAGENTA}{sql}{Fore.RESET}')

            if not dry_run:
                result = cursor.execute(sql)
                LOG.verbose(f'result: {Fore.GREEN}{result}{Fore.RESET}')

        if not dry_run:
            conn.commit()

def update_schemas(agol_meta_map, dry_run=False):
    alter_statements = {}

    with pyodbc.connect(config.get_source_connection()[6:]) as conn:
        sql = """SELECT
    LOWER(table_schema) as table_schema,
    LOWER(table_name) as table_name,
    lower(column_name) as column_name,
    data_type
FROM
    INFORMATION_SCHEMA.COLUMNS c
INNER JOIN meta.AGOLITEMS a ON
    LOWER(a.tablename) = concat('sgid.', LOWER(table_schema), '.', LOWER(table_name))
WHERE
    c.data_type in ('smallint',
    'int',
    'bigint')
    AND column_name not in ('OBJECTID', 'OBJECTID_1')
    AND c.TABLE_SCHEMA not in ('sde',
    'meta')
ORDER BY
    c.table_name;"""

        with conn.cursor() as cursor:
            result = cursor.execute(sql)

            for schema_name, table_name, column, data_type in result:
                pg_table = agol_meta_map[schema_name][table_name]['title']
                pg_table = f'{schema_name}.{pg_table}'

                alter_statements.setdefault(
                    pg_table, []
                ).append(f'ALTER COLUMN {column} TYPE {data_type} USING {column}::{data_type}')

    with psycopg2.connect(**config.DBO_CONNECTION) as conn:
        with conn.cursor() as cursor:
            for table, alter_column_statements in alter_statements.items():
                sql = f'ALTER TABLE {table} {", ".join(alter_column_statements)};'

                LOG.verbose(f'updating schema for {Fore.CYAN}{table}{Fore.RESET} with {Fore.MAGENTA}{sql}{Fore.RESET}')

                if not dry_run:
                    result = cursor.execute(sql)
                    LOG.verbose(f'result: {Fore.GREEN}{result}{Fore.RESET}')

            if not dry_run:
                conn.commit()
