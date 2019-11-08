#!/usr/bin/env python
# * coding: utf8 *
'''
cloudb

Usage:
  cloudb create db [--name=<name> --verbosity=<level>]
  cloudb create schema [--schemas=<name> --verbosity=<level>]
  cloudb create admin-user [--verbosity=<level>]
  cloudb import [--skip-schema=<names>... --dry-run --verbosity=<level> --skip-if-exists]

Arguments:
  name - all or any of the other iso categories
'''

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


def execute_sql(sql, connection):
    LOG.info(f'  executing {sql}')

    with psycopg2.connect(**connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)

        conn.commit()


def create_db(name, owner):
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
    layer_schema_map = []
    exclude_schemas = ['sde', 'meta']
    exclude_fields = ['objectid', 'fid', 'globalid', 'gdb_geomattr_data']

    if skip_schemas and len(skip_schemas) > 0:
        exclude_schemas.extend(skip_schemas)

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

        if schema in exclude_schemas:
            LOG.verbose(f' {Fore.RED}- skipping:{Fore.RESET} {schema}')

            continue

        definition = qualified_layer.GetLayerDefn()

        fields = []
        for field_index in range(definition.GetFieldCount()):
            field = definition.GetFieldDefn(field_index)

            field_name = field.GetName().lower()

            if field_name in exclude_fields:
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
    gdal.SetConfigOption('MSSQLSPATIAL_LIST_ALL_TABLES', 'YES')
    gdal.SetConfigOption('PG_USE_COPY', 'YES')
    gdal.SetConfigOption('PG_USE_POSTGIS', 'YES')
    gdal.SetConfigOption('PG_LIST_ALL_TABLES', 'YES')

    cloud_db = config.format_ogr_connection(config.DBO_CONNECTION)
    internal_sgid = config.get_source_connection()

    layer_schema_map = _get_tables(internal_sgid, skip_schemas)

    LOG.info(f'{Fore.BLUE}inserting layers...{Fore.RESET}')

    for schema, layer, fields in layer_schema_map:
        if if_not_exists and _check_if_exists(cloud_db, schema, layer):
            LOG.info(f' -skipping {Fore.RED}{schema}.{layer}{Fore.RESET}: already exists')
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
                '-lco',
                'GEOM_TYPE=geometry',
                '-lco',
                'PRECISION=YES',
                # '-nlt',
                # 'POLYGON',
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
            result = gdal.VectorTranslate(
                cloud_db,
                internal_sgid,
                options=pg_options
            )

            import pdb; pdb.set_trace()

            del result

        LOG.info(f'{Fore.GREEN}- done{Fore.RESET}')

    LOG.info(f'{Fore.GREEN} Completed!')


def create_public_user(props):
    sql = dedent(
        f'''
        CREATE ROLE {props["name"]} WITH
        LOGIN
        PASSWORD '{props["password"]}'
        NOSUPERUSER
        NOINHERIT
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
                return create_schemas(config.SCHEMAS)

            name = name.lower()

            if name in config.SCHEMAS:
                return create_schemas([name])

        if args['admin-user']:
            return create_admin_user(config.ADMIN)

        if args['db']:
            name = args['--name'] or config.DB

            return create_db(name.lower(), config.DBO)

    if args['import']:
        return import_data(args['--skip-schema'], args['--skip-if-exists'], args['--dry-run'])

    return 1


if __name__ == '__main__':
    main()
