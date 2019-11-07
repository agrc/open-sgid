#!/usr/bin/env python
# * coding: utf8 *
'''
cloudb

Usage:
  cloudb create db [--name=<name>]
  cloudb create schema [--schemas=<name>]
  cloudb create admin-user
  cloudb import [--skip-schema=<names>...]

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


def execute_sql(sql, connection):
    print(f'  executing {sql}')

    with psycopg2.connect(**connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)

        conn.commit()


def create_db(name, owner):
    print(f'creating database {name}')

    sql = dedent(f'''
        CREATE DATABASE {name}
        WITH
        OWNER = {owner}
        ENCODING = 'UTF8'
        CONNECTION LIMIT = -1;
    ''')

    admin_connection = config.DBO_CONNECTION
    admin_connection['database'] = 'postgres'

    print(f'  executing {sql}')

    with psycopg2.connect(**admin_connection) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cursor:
            cursor.execute(sql)

    print('enabling postgis')

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

        print(f'creating schemas for {sql}')
        with conn.cursor() as cursor:
            cursor.execute(';'.join(sql))

        conn.commit()

def _get_tables(connection, skip_schemas):
    layer_schema_map = []
    exclude_schemas = ['sde', 'meta']
    exclude_fields = ['objectid', 'fid', 'globalid', 'gdb_geomattr_data']

    if skip_schemas and len(skip_schemas) > 0:
        exclude_schemas.extend(skip_schemas)

    for qualified_layer in connection:
        schema, layer = qualified_layer.GetName().split('.')
        schema = schema.lower()
        layer = layer.lower()

        print(f'checking {Fore.BLUE}{schema}.{layer}{Fore.RESET}...')

        if schema in exclude_schemas:
            print(f'{Fore.RED}- skipping:{Fore.RESET} {schema}')

            continue

        definition = qualified_layer.GetLayerDefn()

        fields = []
        for field_index in range(definition.GetFieldCount()):
            field = definition.GetFieldDefn(field_index)

            field_name = field.GetName().lower()

            if field_name in exclude_fields:
                print(f'  {Fore.YELLOW}- skipping:{Fore.RESET} {field_name}')

                field.Destroy()

                continue

            fields.append(field_name)

            field.Destroy()

        layer_schema_map.append((schema, layer, fields))

        del definition
        del qualified_layer

    print(f'sorting map. found {Fore.GREEN}{len(layer_schema_map)}{Fore.RESET} layers')
    layer_schema_map.sort(key=lambda items: items[0])

    return layer_schema_map


def import_data(skip_schemas):
    gdal.UseExceptions()
    gdal.SetConfigOption('PG_USE_COPY', 'YES')

    cloud_db = config.format_ogr_connection(config.DBO_CONNECTION)
    internal_sgid = config.get_source_connection()

    connection = ogr.Open(internal_sgid)

    layer_schema_map = _get_tables(connection, skip_schemas)

    print(f'{Fore.BLUE}inserting layers...{Fore.RESET}')

    for schema, layer, fields in layer_schema_map:

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

        print(f'  inserting {Fore.MAGENTA}{layer}{Fore.RESET} into {Fore.BLUE}{schema}{Fore.RESET} with {Fore.CYAN}{sql}{Fore.RESET}...')

        result = gdal.VectorTranslate(
            cloud_db,
            internal_sgid,
            options=pg_options
        )

        print(f'{Fore.GREEN}- done{Fore.RESET}')

        del result


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
    print(f'{Back.WHITE}{Fore.BLACK}{args}{Back.RESET}{Fore.RESET}')

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
        return import_data(args['--skip-schema'])

    return 1


if __name__ == '__main__':
    main()
