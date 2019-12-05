#!/usr/bin/env python
# * coding: utf8 *
'''
roles.py
A module that allows for role modifications
'''

from textwrap import dedent

import psycopg2
from colorama import Fore

from .__main__ import LOG, config, execute_sql


def create_read_only_user(schemas):
    '''create public user
    '''

    LOG.info(f'creating {Fore.CYAN}read only{Fore.RESET} role')

    with psycopg2.connect(**config.DBO_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='read_only'")
            role = cursor.fetchone()

            if role is None or role[0] != 1:
                sql = dedent(
                    f'''
                        CREATE ROLE read_only WITH
                        NOSUPERUSER
                        NOCREATEDB
                        NOCREATEROLE
                        NOINHERIT
                        NOLOGIN
                        NOREPLICATION
                        VALID UNTIL 'infinity';

                        -- grant privileges

                        GRANT CONNECT ON DATABASE {config.DB} TO read_only;
                        GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO read_only;
                        GRANT USAGE ON SCHEMA public TO read_only;
                        '''
                )

                execute_sql(sql, config.DBO_CONNECTION)

            conn.commit()

    sql = []

    for name in schemas:
        sql.append(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {name} GRANT SELECT ON TABLES TO read_only')
        sql.append(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {name} GRANT EXECUTE ON FUNCTIONS TO read_only')
        sql.append(f'ALTER DEFAULT PRIVILEGES GRANT USAGE ON SCHEMAS TO read_only')
        sql.append(f'GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA {name} TO read_only')
        sql.append(f'GRANT SELECT ON ALL TABLES IN SCHEMA {name} TO read_only')
        sql.append(f'GRANT USAGE ON SCHEMA {name} TO read_only')

    execute_sql(';'.join(sql), config.DBO_CONNECTION)

    LOG.info(f'adding {Fore.CYAN}agrc{Fore.RESET} user to {Fore.MAGENTA}read only{Fore.RESET} role')

    sql = dedent(
        f'''
        DROP ROLE IF EXISTS agrc;
        CREATE ROLE agrc WITH
        LOGIN
        PASSWORD 'agrc'
        IN ROLE read_only
        VALID UNTIL 'infinity';
        '''
    )

    execute_sql(sql, config.DBO_CONNECTION)


def create_admin_user(props):
    '''creates the admin user that owns the schemas
    props: dictionary with credentials for user
    '''
    sql = dedent(
        f'''
        CREATE ROLE {props["name"]} WITH
        LOGIN
        PASSWORD '{props["password"]}'
        NOSUPERUSER
        INHERIT
        NOCREATEDB
        NOCREATEROLE
        NOREPLICATION
        VALID UNTIL 'infinity';

        COMMENT ON ROLE {props["name"]} IS 'Owner of all schemas';

        -- grant admin permissions

        GRANT {props["name"]} TO postgres;
    '''
    )

    execute_sql(sql, config.DBO_CONNECTION)
