#!/usr/bin/env python
# * coding: utf8 *
'''
schema.py
A module that modifies schemas
'''

import psycopg2
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
