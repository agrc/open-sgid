#!/usr/bin/env python
# * coding: utf8 *
'''
cloudb

Usage:
  cloudb enable postgis [--verbosity=<level>]
  cloudb create schema [--schemas=<name> --verbosity=<level>]
  cloudb create admin-user [--verbosity=<level>]
  cloudb create read-only-user [--verbosity=<level>]
  cloudb drop schema [--schemas=<name> --verbosity=<level>]
  cloudb import [--missing --dry-run --verbosity=<level> --skip-if-exists]
  cloudb trim [--dry-run --verbosity=<level>]
  cloudb update [--table=<tables>... --dry-run --verbosity=<level>]

Arguments:
  name - all or any of the other iso categories
'''

import sys
from time import perf_counter

import psycopg2
from colorama import Back, Fore, init
from docopt import docopt
from osgeo import gdal, ogr

import pyodbc

from . import CONNECTION_TABLE_CACHE, LOG, config, roles, schema, utils

gdal.SetConfigOption('MSSQLSPATIAL_LIST_ALL_TABLES', 'YES')
gdal.SetConfigOption('PG_LIST_ALL_TABLES', 'YES')
gdal.SetConfigOption('PG_USE_POSTGIS', 'YES')
gdal.SetConfigOption('PG_USE_COPY', 'YES')


def execute_sql(sql, connection):
    '''executes sql on the information
    sql: string T-SQL
    connection: dict with connection information
    '''
    LOG.debug(f'  executing {sql}')

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


def _get_tables_with_fields(connection_string, specific_tables):
    '''creates a list of tables with fields from the connection string
    connection_string: string to connect to db
    specific_tables: array of tables to get
    returns: array of tuples with 0: schema, 1: table name: 2: array of field names
    '''
    layer_schema_map = []
    filter_tables = False

    if specific_tables and len(specific_tables) > 0:
        LOG.debug(f'{Fore.CYAN}filtering for specific tables{Fore.RESET}')

        filter_tables = True

    LOG.verbose('connecting to database')
    connection = gdal.OpenEx(connection_string)

    LOG.verbose('getting layer count')
    table_count = connection.GetLayerCount()

    LOG.info(f'discovered {Fore.YELLOW}{table_count}{Fore.RESET} tables')

    for table_index in range(table_count):
        qualified_layer = connection.GetLayerByIndex(table_index)
        schema_name, layer = qualified_layer.GetName().split('.')
        schema_name = schema_name.lower()
        layer = layer.lower()

        LOG.debug(f'- {Fore.CYAN}{schema_name}.{layer}{Fore.RESET}')

        if schema_name in config.EXCLUDE_SCHEMAS or filter_tables and layer not in specific_tables:
            LOG.verbose(f' {Fore.RED}- skipping:{Fore.RESET} {schema_name}')

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

        layer_schema_map.append((schema_name, layer, fields))

        del qualified_layer

    LOG.info(f'planning to import {Fore.GREEN}{len(layer_schema_map)}{Fore.RESET} tables')
    layer_schema_map.sort(key=lambda items: items[0])

    connection = None

    return layer_schema_map


def _get_schema_table_name_map(table_name):
    '''a method to split a qualified table into it's parts
    '''
    parts = table_name.split('.')

    schema_index = 1
    table_index = 2

    if len(parts) == 2:
        schema_index = 0
        table_index = 1

    return {'schema': parts[schema_index].lower(), 'table_name': parts[table_index].lower()}


def _format_title_for_pg(title):
    if title is None:
        return title

    new_title = title.lower()
    new_title = new_title.replace('utah ', '', 1).replace(' ', '_')

    LOG.verbose(f'updating {Fore.MAGENTA}{title}{Fore.RESET} to {Fore.CYAN}{new_title}{Fore.RESET}')

    return new_title


def _get_table_meta():
    '''gets the meta data about fields from meta.agolitems
    '''
    mapping = {}

    with pyodbc.connect(config.get_source_connection()[6:]) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT [TABLENAME],[AGOL_PUBLISHED_NAME],[GEOMETRY_TYPE] FROM [SGID].[META].[AGOLITEMS]")
        rows = cursor.fetchall()

        #: table: SGID.ENVIRONMENT.DAQPermitCompApproval
        #: title: Utah Retail Culinary Water Service Areas
        #: geometry_type: POINT POLYGON POLYLINE
        for table, title, geometry_type in rows:
            table_parts = _get_schema_table_name_map(table)
            pg_title = _format_title_for_pg(title)

            schema_name = mapping.setdefault(table_parts['schema'], {})
            schema_name[table_parts['table_name']] = {'title': pg_title, 'geometry_type': geometry_type}

        return mapping


def _populate_table_cache(connection_string, pgify=False, name_map=None):
    '''adds all the table from a connection string to a dictionary for caching purposes
    pgify: lowercases and adds underscores
    name_map: is a dictionary to replace names from the meta table
    '''
    skip_schema = ['meta', 'sde']
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
            LOG.verbose(f'qualified layer name: {name}')

            if '.' not in name:
                continue

            table_parts = _get_schema_table_name_map(name)
            name = f"{table_parts['schema']}.{table_parts['table_name']}"

            if table_parts['schema'] in skip_schema:
                continue

            if pgify:
                pg_title = _format_title_for_pg(table_parts['table_name'])
                schema_name = table_parts['schema']

                if schema_name in name_map and pg_title in name_map[schema_name]:
                    table, _ = name_map[schema_name][pg_title].values()
                name = f"{schema_name}.{table}"

            LOG.verbose(f'found layer: {name}')

            CONNECTION_TABLE_CACHE[connection_string].append(name)

    del qualified_layer
    connection = None


def _check_if_exists(connection_string, schema_name, table, agol_meta_map):
    '''returns true or false if a table exists in the connections_string db
    connection_string: string of db to check
    schema_name: string schema name
    table: string table name
    returns: bool
    '''
    LOG.debug('checking cache')

    if schema_name in agol_meta_map and table in agol_meta_map[schema_name]:
        table, _ = agol_meta_map[schema_name][table].values()

    if connection_string in CONNECTION_TABLE_CACHE and len(CONNECTION_TABLE_CACHE[connection_string]) > 0:
        LOG.verbose('cache hit')

        return f'{schema_name}.{table}' in CONNECTION_TABLE_CACHE[connection_string]

    LOG.verbose('cache miss')
    _populate_table_cache(connection_string)

    found = False
    if f'{schema}.{table}' in CONNECTION_TABLE_CACHE[connection_string]:
        found = True

    return found


def _replace_data(schema_name, layer, fields, agol_meta_map, dry_run):
    '''the insert logic for writing to the destination
    '''
    cloud_db = config.format_ogr_connection(config.DBO_CONNECTION)
    internal_sgid = config.get_source_connection()

    sql = f'SELECT objectid FROM "{schema_name}.{layer}"'

    if len(fields) > 0:
        #: escape reserved words?
        fields = [f'"{field}"' for field in fields]
        sql = f"SELECT {','.join(fields)} FROM \"{schema_name}.{layer}\""

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
        f'SCHEMA={schema_name}',
        '-lco',
        'OVERWRITE=YES',
        '-lco',
        'GEOMETRY_NAME=shape',
        '-lco',
        'PRECISION=YES',
        '-a_srs',
        config.UTM,
    ]

    if schema_name in agol_meta_map and layer in agol_meta_map[schema_name]:
        new_name, geometry_type = agol_meta_map[schema_name][layer].values()

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

    pg_options = gdal.VectorTranslateOptions(options=options)

    LOG.info(f'- inserting {Fore.MAGENTA}{layer}{Fore.RESET} into {Fore.BLUE}{schema_name}{Fore.RESET} as {Fore.CYAN}{geometry_type}{Fore.RESET}')
    LOG.debug(f'with {Fore.CYAN}{sql}{Fore.RESET}')

    if not dry_run:
        start_seconds = perf_counter()
        result = gdal.VectorTranslate(cloud_db, internal_sgid, options=pg_options)
        LOG.debug(f'- {Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

        del result

        LOG.debug(f'- {Fore.CYAN}make valid{Fore.RESET}')
        make_valid(f'{schema_name}.{layer}')


def import_data(if_not_exists, missing_only, dry_run):
    '''imports data from sql to postgis
    if_not_exists: create new tables if the destination does not have it
    dry_run: do not modify the destination
    '''
    cloud_db = config.format_ogr_connection(config.DBO_CONNECTION)
    internal_sgid = config.get_source_connection()

    tables = []
    if missing_only:
        source, destination = _get_table_sets()
        tables = destination - source

        LOG.info(f'there are {Fore.CYAN}{len(tables)}{Fore.RESET} tables in the source not in the destination')

        if len(tables) == 0:
            return

    layer_schema_map = _get_tables_with_fields(internal_sgid, tables)
    agol_meta_map = _get_table_meta()

    for schema_name, layer, fields in layer_schema_map:
        if if_not_exists and _check_if_exists(cloud_db, schema_name, layer, agol_meta_map):
            LOG.info(f'- skipping {Fore.MAGENTA}{schema_name}.{layer} {Fore.CYAN}already exists{Fore.RESET}')

            continue

        _replace_data(schema_name, layer, fields, agol_meta_map, dry_run)


def _get_table_sets():
    '''gets a set of each schema.tablename from the source and destination database to help figure out what is different between them
    '''
    cloud_db = config.format_ogr_connection(config.DBO_CONNECTION)
    internal_sgid = config.get_source_connection()

    if cloud_db not in CONNECTION_TABLE_CACHE:
        _populate_table_cache(cloud_db)

    if internal_sgid not in CONNECTION_TABLE_CACHE:
        _populate_table_cache(internal_sgid, pgify=True, name_map=_get_table_meta())

    source = set(CONNECTION_TABLE_CACHE[cloud_db])
    destination = set(CONNECTION_TABLE_CACHE[internal_sgid])

    return source, destination


def trim(dry_run):
    '''get source tables with updated names
    get destination tables with original names
    drop the tables in the destination found in the difference between the two sets
    '''

    source, destination = _get_table_sets()
    items_to_trim = source - destination

    LOG.info(f'there are {Fore.CYAN}{len(items_to_trim)}{Fore.RESET} tables in the destination not in the source')

    if len(items_to_trim) == 0:
        return

    sql = f'DROP TABLE {",".join(items_to_trim)}'
    LOG.info(f'dropping {items_to_trim}')

    if not dry_run:
        execute_sql(sql, config.DBO_CONNECTION)

    LOG.info(f'{Fore.GREEN}finished{Fore.RESET}')


def update(specific_tables, dry_run):
    '''update specific tables in the destination
    specific_tables: a list of tables from the source without the schema
    dry_run: bool if insertion should actually happen
    '''
    internal_sgid = config.get_source_connection()

    if not specific_tables or len(specific_tables) == 0:
        LOG.info(f'{Fore.YELLOW} no tables to import!{Fore.RESET}')

        return

    layer_schema_map = _get_tables_with_fields(internal_sgid, specific_tables)

    if len(layer_schema_map) == 0:
        LOG.info(f'{Fore.YELLOW} no matching table found!{Fore.RESET}')

        return

    agol_meta_map = _get_table_meta()

    if len(specific_tables) != len(layer_schema_map):
        LOG.warn((
            f'{Back.YELLOW}{Fore.BLACK}input {len(specific_tables)} tables but only {len(layer_schema_map)} found.{Fore.RESET}{Back.RESET} '
            'check your spelling'
        ))

    for schema_name, layer, fields in layer_schema_map:
        _replace_data(schema_name, layer, fields, agol_meta_map, dry_run)


def make_valid(layer):
    '''update invalid shapes in postgres
    '''
    sql = f'UPDATE {layer} SET shape = ST_MakeValid(shape) WHERE ST_IsValid(shape) = false;'

    try:
        execute_sql(sql, config.DBO_CONNECTION)
    except psycopg2.errors.UndefinedColumn:
        #: table doesn't have shape field
        pass

def main():
    '''Main entry point for program. Parse arguments and pass to sweeper modules.
    '''
    init()
    args = docopt(__doc__, version='1.0.0')

    start_seconds = perf_counter()

    LOG.init(args['--verbosity'])
    LOG.debug(f'{Back.WHITE}{Fore.BLACK}{args}{Back.RESET}{Fore.RESET}')

    if args['enable']:
        enable_postgis()

        LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

        sys.exit()

    if args['create']:
        if args['schema']:
            name = args['--schemas']

            if name is None or name == 'all':
                schema.create_schemas(config.SCHEMAS)
                sys.exit()

            name = name.lower()

            if name in config.SCHEMAS:
                schema.create_schemas([name])
                sys.exit()

        if args['admin-user']:
            roles.create_admin_user(config.ADMIN)

            LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

            sys.exit()

        if args['read-only-user']:
            roles.create_read_only_user(config.SCHEMAS)

            LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

            sys.exit()

    if args['drop']:
        if args['schema']:
            name = args['--schemas']

            if name is None or name == 'all':
                schema.drop_schemas(config.SCHEMAS)

                LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

                sys.exit()

            name = name.lower()

            if name in config.SCHEMAS:
                schema.drop_schemas([name])

                LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

                sys.exit()

    if args['import']:
        import_data(args['--skip-if-exists'], args['--missing'], args['--dry-run'])

        LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

        sys.exit()

    if args['trim']:
        trim(args['--dry-run'])

        LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

        sys.exit()

    if args['update']:
        update(args['--table'], args['--dry-run'])

        LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

        sys.exit()

    LOG.info(f'{Fore.GREEN}completed{Fore.RESET} in {Fore.CYAN}{utils.format_time(perf_counter() - start_seconds)}{Fore.RESET}')

    sys.exit()


if __name__ == '__main__':
    main()
