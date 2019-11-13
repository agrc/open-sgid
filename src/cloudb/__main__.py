#!/usr/bin/env python
# * coding: utf8 *
'''
cloudb

Usage:
  cloudb create db [--name=<name> --verbosity=<level>]
  cloudb create schema [--schemas=<name> --verbosity=<level>]
  cloudb create admin-user [--verbosity=<level>]
  cloudb create read-only-user [--verbosity=<level>]
  cloudb import [--skip-schema=<names>... --dry-run --verbosity=<level> --skip-if-exists]
  cloudb fix-geometries [--verbosity=<level>]

Arguments:
  name - all or any of the other iso categories
'''

import sys
from textwrap import dedent

import psycopg2
from colorama import Back, Fore, init
from docopt import docopt
from osgeo import gdal, ogr
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from . import config
from .logger import Logger

LOG = Logger()
CONNECTION_TABLE_CACHE = {}

gdal.SetConfigOption('MSSQLSPATIAL_LIST_ALL_TABLES', 'YES')
gdal.SetConfigOption('PG_LIST_ALL_TABLES', 'YES')
gdal.SetConfigOption('PG_USE_POSTGIS', 'YES')
gdal.SetConfigOption('PG_USE_COPY', 'YES')


def execute_sql(sql, connection):
    '''executes sql on the information
    sql: string T-SQL
    connection: dict with connection information
    '''
    LOG.info(f'  executing {sql}')

    with psycopg2.connect(**connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)

        conn.commit()


def create_db(name, owner):
    '''creates the database with the postgis extension
    name: string db name
    owner: string db owner
    '''
    LOG.info(f'creating database {name}')

    sql = dedent(f'''
        CREATE DATABASE {name}
        WITH
        OWNER = {owner}
        ENCODING = 'UTF8'
        CONNECTION LIMIT = -1;
    ''')

    admin_connection = config.DBO_CONNECTION
    admin_connection['database'] = 'postgres'

    LOG.info(f'  executing {sql}')

    with psycopg2.connect(**admin_connection) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cursor:
            cursor.execute(sql)

    LOG.info('enabling postgis')

    execute_sql('CREATE EXTENSION postgis;', config.DBO_CONNECTION)


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


def _get_tables(connection_string, skip_schemas):
    '''creates a list of tables with fields from the connection string
    connection_string: string to connect to db
    skip_schemas: array of schemas to ignore when building the list
    returns: array of tuples with 0: schema, 1: table name: 2: array of field names
    '''
    layer_schema_map = []

    if skip_schemas and len(skip_schemas) > 0:
        config.EXCLUDE_SCHEMAS.extend(skip_schemas)

    LOG.verbose('connecting to database')
    connection = gdal.OpenEx(connection_string)

    LOG.verbose('getting layer count')
    table_count = connection.GetLayerCount()

    LOG.info(f'found {Fore.YELLOW}{table_count}{Fore.RESET} total tables')

    for table_index in range(table_count):
        qualified_layer = connection.GetLayerByIndex(table_index)
        schema, layer = qualified_layer.GetName().split('.')
        schema = schema.lower()
        layer = layer.lower()

        LOG.debug(f'- {Fore.CYAN}{schema}.{layer}{Fore.RESET}')

        if schema in config.EXCLUDE_SCHEMAS:
            LOG.verbose(f' {Fore.RED}- skipping:{Fore.RESET} {schema}')

            continue

        definition = qualified_layer.GetLayerDefn()

        fields = []
        for field_index in range(definition.GetFieldCount()):
            field = definition.GetFieldDefn(field_index)

            field_name = field.GetName().lower()

            if field_name in config.EXCLUDE_FIELDS:
                LOG.verbose(f'  {Fore.YELLOW}- skipping:{Fore.RESET} {field_name}')

                continue

            fields.append(field_name)

        layer_schema_map.append((schema, layer, fields))

        del qualified_layer

    LOG.info(f'found {Fore.GREEN}{len(layer_schema_map)}{Fore.RESET} tables for import')
    layer_schema_map.sort(key=lambda items: items[0])

    connection = None

    return layer_schema_map


def _check_if_exists(connection_string, schema, table):
    '''returns true or false if a table exists in the connections_string db
    connection_string: string of db to check
    schema: string schema name
    table: string table name
    returns: bool
    '''
    LOG.debug('checking cache')

    if connection_string in CONNECTION_TABLE_CACHE and len(CONNECTION_TABLE_CACHE[connection_string]) > 0:
        LOG.verbose('cache populated')
        return f'{schema}.{table}' in CONNECTION_TABLE_CACHE[connection_string]

    LOG.verbose('connecting to database')
    #: gdal.open gave a 0 table count
    connection = ogr.Open(connection_string)

    LOG.verbose('getting layer count')
    table_count = connection.GetLayerCount()

    LOG.debug(f'found {Fore.YELLOW}{table_count}{Fore.RESET} total tables for cache')
    CONNECTION_TABLE_CACHE.setdefault(connection_string, [])

    for table_index in range(table_count):
        qualified_layer = connection.GetLayerByIndex(table_index)

        if qualified_layer:
            name = qualified_layer.GetName()

            LOG.verbose(f'found layer: {name}')

            CONNECTION_TABLE_CACHE[connection_string].append(name)

    found = False
    if f'{schema}.{table}' in CONNECTION_TABLE_CACHE[connection_string]:
        found = True

    del qualified_layer
    connection = None

    return found


def import_data(skip_schemas, if_not_exists, dry_run):
    '''imports data from sql to postgis
    skip_schemas: array of schema strings to skip
    if_not_exists: create new tables if the destination does not have it
    dry_run: do not modify the destination
    '''
    cloud_db = config.format_ogr_connection(config.DBO_CONNECTION)
    internal_sgid = config.get_source_connection()

    layer_schema_map = _get_tables(internal_sgid, skip_schemas)

    LOG.info(f'{Fore.BLUE}inserting layers...{Fore.RESET}')

    for schema, layer, fields in layer_schema_map:
        if if_not_exists and _check_if_exists(cloud_db, schema, layer):
            LOG.debug(f' -skipping {Fore.RED}{schema}.{layer}{Fore.RESET}: already exists')

            continue

        sql = f'SELECT objectid FROM "{schema}.{layer}"'

        if len(fields) > 0:
            #: escape reserved words?
            fields = [f'"{field}"' for field in fields]
            sql = f"SELECT {','.join(fields)} FROM \"{schema}.{layer}\""

        pg_options = gdal.VectorTranslateOptions(
            options=[
                '-f',
                'PostgreSQL',
                '-dialect',
                'OGRSQL',
                '-sql',
                sql,
                '-lco',
                'FID=xid',
                '-lco',
                f'SCHEMA={schema}',
                '-lco',
                'OVERWRITE=YES',
                '-lco',
                'GEOMETRY_NAME=shape',
                # '-lco',
                # 'GEOM_TYPE=geometry',
                '-lco',
                'PRECISION=YES',
                '-nlt',
                'PROMOTE_TO_MULTI',
                '-nln',
                f'{layer}',
                '-s_srs',
                config.UTM,
                '-spat_srs',
                config.UTM,
            ],
        )

        LOG.info(f'inserting {Fore.MAGENTA}{layer}{Fore.RESET} into {Fore.BLUE}{schema}{Fore.RESET}')
        LOG.debug(f'with {Fore.CYAN}{sql}{Fore.RESET}')

        if not dry_run:
            result = gdal.VectorTranslate(cloud_db, internal_sgid, options=pg_options)

            del result

        LOG.info(f'{Fore.GREEN}- done{Fore.RESET}')

    LOG.info(f'{Fore.GREEN} Completed!')


def update_geometry_type(connection):
    '''checks for a shape field and alters the table to match the geometry type
    connection: dict of connection properties
    '''

    with psycopg2.connect(**connection) as conn:
        with conn.cursor() as cursor:
            get_geometry_tables = (
                'SELECT f_table_schema,f_table_name,f_geometry_column FROM public.geometry_columns '
                'WHERE "type"=\'GEOMETRY\' ORDER BY f_table_schema,f_table_name;'
            )

            cursor.execute(get_geometry_tables)
            tables_with_geometry_type = cursor.fetchall()

            for schema, table_name, shape_field in tables_with_geometry_type:
                LOG.debug(f'getting geometry types from {Fore.CYAN}{schema}.{table_name}{Fore.RESET}')

                cursor.execute(f'SELECT DISTINCT geometrytype({shape_field}) FROM {schema}.{table_name}')

                geometry_type = None
                count = cursor.rowcount

                LOG.debug(f'found {Fore.CYAN}{count}{Fore.RESET} geometry type')

                if count == 1:
                    geometry_type, = cursor.fetchone()
                    LOG.verbose(f'found {Fore.MAGENTA}{geometry_type}{Fore.RESET}')

                    if geometry_type is None:
                        #: delete shape field; stand alone table
                        LOG.info(f'no shape type found on {Fore.CYAN}{schema}.{table_name}{Fore.RESET}. {Fore.RED}dropping shape field{Fore.RESET}')

                        cursor.execute(f'ALTER TABLE {schema}.{table_name} DROP COLUMN {shape_field} CASCADE')
                        conn.commit()

                        continue
                else:
                    geometry_types = [geom[0] for geom in cursor.fetchall()]

                    LOG.verbose(f'found {Fore.MAGENTA}{", ".join(geometry_types)}{Fore.RESET}')

                    geometry_type = max(geometry_types, key=len)

                    LOG.verbose(f'chose {Fore.GREEN}{geometry_type}{Fore.RESET}')

                set_geometry_type = (
                    f'ALTER TABLE {schema}.{table_name} '
                    f'ALTER COLUMN {shape_field} TYPE GEOMETRY({geometry_type}) '
                    f'USING ST_SetSRID({shape_field},26912);'
                )

                if 'multi' in geometry_type.lower():
                    LOG.verbose(f'{Fore.CYAN}upgrading to {geometry_type.lower()}{Fore.RESET}')

                    upgrade_to_multi = (
                        f'ALTER TABLE {schema}.{table_name} '
                        f'ALTER COLUMN {shape_field} TYPE GEOMETRY({geometry_type}) '
                        f'USING ST_Multi({shape_field});'
                    )

                    cursor.execute(upgrade_to_multi)
                    conn.commit()

                cursor.execute(set_geometry_type)
                conn.commit()


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


def main():
    '''Main entry point for program. Parse arguments and pass to sweeper modules.
    '''
    init()
    args = docopt(__doc__, version='1.0.0')

    LOG.init(args['--verbosity'])
    LOG.debug(f'{Back.WHITE}{Fore.BLACK}{args}{Back.RESET}{Fore.RESET}')

    if args['create']:
        if args['schema']:
            name = args['--schemas']

            if name is None or name == 'all':
                create_schemas(config.SCHEMAS)
                sys.exit()

            name = name.lower()

            if name in config.SCHEMAS:
                create_schemas([name])
                sys.exit()

        if args['admin-user']:
            create_admin_user(config.ADMIN)
            sys.exit()

        if args['read-only-user']:
            create_read_only_user(config.SCHEMAS)

        if args['db']:
            name = args['--name'] or config.DB

            create_db(name.lower(), config.DBO)

            sys.exit()

    if args['import']:
        import_data(args['--skip-schema'], args['--skip-if-exists'], args['--dry-run'])

        sys.exit()

    if args['fix-geometries']:
        update_geometry_type(config.DBO_CONNECTION)
        sys.exit()

    sys.exit()


if __name__ == '__main__':
    main()
