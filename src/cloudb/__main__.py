#!/usr/bin/env python
# * coding: utf8 *
'''
cloudb

Usage:
  cloudb enable postgis [--verbosity=<level>]
  cloudb create schema [--schemas=<name> --verbosity=<level>]
  cloudb create admin-user [--verbosity=<level>]
  cloudb create read-only-user [--verbosity=<level>]
  cloudb import [--skip-schema=<names>... --dry-run --verbosity=<level> --skip-if-exists]

Arguments:
  name - all or any of the other iso categories
'''

import sys
from textwrap import dedent

import psycopg2
from colorama import Back, Fore, init
from docopt import docopt
from osgeo import gdal, ogr
import pyodbc

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


def enable_postgis():
    '''enables the postgis extension
    owner: string db owner
    '''
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


def _get_table_meta():
    '''gets the meta data about fields from meta.agolitems
    '''
    def get_schema_table_name_map(table_name):
        parts = table_name.split('.')

        if len(parts) != 3:
            LOG.warn(f'{table_name} does not fit the db.owner.name convention')

        return {'schema': parts[1].lower(), 'table_name': parts[2].lower()}

    def format_title_for_pg(title):
        if title is None:
            return title

        new_title = title.lower()
        new_title = new_title.replace('utah ', '').replace(' ', '_', 100)

        LOG.verbose(f'updating {Fore.MAGENTA}{title}{Fore.RESET} to {Fore.CYAN}{new_title}{Fore.RESET}')

        return new_title

    mapping = {}

    with pyodbc.connect(config.get_source_connection()[6:]) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT [TABLENAME],[AGOL_PUBLISHED_NAME],[GEOMETRY_TYPE] FROM [SGID].[META].[AGOLITEMS]")
        rows = cursor.fetchall()

        #: table: SGID.ENVIRONMENT.DAQPermitCompApproval
        #: title: Utah Retail Culinary Water Service Areas
        #: geometry_type: POINT POLYGON POLYLINE
        for table, title, geometry_type in rows:
            table_parts = get_schema_table_name_map(table)
            pg_title = format_title_for_pg(title)

            schema = mapping.setdefault(table_parts['schema'], {})
            schema[table_parts['table_name']] = {'title': pg_title, 'geometry_type': geometry_type}

        return mapping


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
    agol_meta_map = _get_table_meta()

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

        options = [
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
            '-lco',
            'PRECISION=YES',
            '-a_srs',
            config.UTM,
        ]

        if schema in agol_meta_map and layer in agol_meta_map[schema]:
            new_name, geometry_type = agol_meta_map[schema][layer].values()

            if new_name:
                layer = new_name

            if geometry_type == 'POLYGON':
                options.append('-nlt')
                options.append('MULTIPOLYGON')
            elif geometry_type == 'POLYLINE':
                options.append('-nlt')
                options.append('MULTILINESTRING')
            elif geometry_type == 'STAND ALONE':
                options.append('-nlt')
                options.append('NONE')
            else:
                options.append('-nlt')
                options.append(geometry_type)

        options.append('-nln')
        options.append(f'{layer}')

        pg_options = gdal.VectorTranslateOptions(
            options=options,
        )

        LOG.info(f'inserting {Fore.MAGENTA}{layer}{Fore.RESET} into {Fore.BLUE}{schema}{Fore.RESET} as {Fore.CYAN}{geometry_type}{Fore.RESET}')
        LOG.debug(f'with {Fore.CYAN}{sql}{Fore.RESET}')

        if not dry_run:
            result = gdal.VectorTranslate(cloud_db, internal_sgid, options=pg_options)

            del result

        LOG.info(f'{Fore.GREEN}- done{Fore.RESET}')

    LOG.info(f'{Fore.GREEN} Completed!')


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

    if args['enable']:
        enable_postgis()

        sys.exit()

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

    if args['import']:
        import_data(args['--skip-schema'], args['--skip-if-exists'], args['--dry-run'])

        sys.exit()

    sys.exit()


if __name__ == '__main__':
    main()
