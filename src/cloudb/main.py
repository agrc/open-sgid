#!/usr/bin/env python
# * coding: utf8 *
"""
cloudb

Usage:
  cloudb enable extensions
  cloudb create schema [--schemas=<name>]
  cloudb create admin-user
  cloudb create read-only-user
  cloudb create indexes
  cloudb drop schema [--schemas=<name>]
  cloudb import [--missing --dry-run --skip-if-exists]
  cloudb trim [--dry-run]
  cloudb update [--table=<tables>... --dry-run --from-change-detection]
  cloudb update-schema [--table=<tables>... --dry-run]
"""

import logging
import sys
from datetime import datetime
from time import perf_counter

import psycopg2
import pyodbc
from docopt import docopt
from google.cloud import storage
from osgeo import gdal, ogr

from . import CONNECTION_TABLE_CACHE, config, execute_sql, roles, schema, utils
from .index import INDEXES

gdal.SetConfigOption('MSSQLSPATIAL_LIST_ALL_TABLES', 'YES')
gdal.SetConfigOption('PG_LIST_ALL_TABLES', 'YES')
gdal.SetConfigOption('PG_USE_POSTGIS', 'YES')
gdal.SetConfigOption('PG_USE_COPY', 'YES')


def enable_extensions():
    """enable the database extension
    owner: string db owner
    """
    logging.info('enabling extensions')

    execute_sql('CREATE EXTENSION postgis;CREATE EXTENSION pg_stat_statements;', config.DBO_CONNECTION)


def _get_tables_with_fields(connection_string, specific_tables):
    """creates a list of tables with fields from the connection string
    connection_string: string to connect to db
    specific_tables: array of tables to get in schema.table format
    returns: array of tuples with 0: schema, 1: table name: 2: array of field names
    """
    layer_schema_map = []
    filter_tables = False

    if specific_tables and len(specific_tables) > 0:
        logging.debug('filtering for specific tables')

        filter_tables = True

    logging.debug('connecting to database')
    connection = gdal.OpenEx(connection_string)

    logging.debug('getting layer count')
    table_count = connection.GetLayerCount()

    logging.info('discovered %s tables', table_count)

    for table_index in range(table_count):
        qualified_layer = connection.GetLayerByIndex(table_index)
        schema_name, layer = qualified_layer.GetName().split('.')
        schema_name = schema_name.lower()
        layer = layer.lower()

        logging.debug('- %s.%s', schema_name, layer)

        if schema_name in config.EXCLUDE_SCHEMAS or filter_tables and f'{schema_name}.{layer}' not in specific_tables:
            logging.debug(' - skipping: %s', schema_name)

            continue

        definition = qualified_layer.GetLayerDefn()

        fields = []
        for field_index in range(definition.GetFieldCount()):
            field = definition.GetFieldDefn(field_index)

            field_name = field.GetName().lower()

            if field_name in config.EXCLUDE_FIELDS:
                logging.debug('  - skipping: %s', field_name)

                continue

            fields.append(field_name)

        layer_schema_map.append((schema_name, layer, fields))

        del qualified_layer

    schema_map_count = len(layer_schema_map)
    noun = 'tables'
    if schema_map_count == 1:
        noun = 'table'

    logging.info('planning to import %s %s', schema_map_count, noun)
    layer_schema_map.sort(key=lambda items: items[0])

    connection = None

    return layer_schema_map


def _get_schema_table_name_map(table_name):
    """a method to split a qualified table into it's parts
    """
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

    logging.debug('updating %s to %s', title, new_title)

    return new_title


def _get_table_meta():
    """gets the meta data about fields from meta.agolitems
    """
    mapping = {}

    with pyodbc.connect(config.get_source_connection()[6:]) as connection:
        cursor = connection.cursor()

        cursor.execute('SELECT [TABLENAME],[AGOL_PUBLISHED_NAME],[GEOMETRY_TYPE] FROM [SGID].[META].[AGOLITEMS]')
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
    """adds all the table from a connection string to a dictionary for caching purposes
    pgify: lowercases and adds underscores
    name_map: is a dictionary to replace names from the meta table
    """
    skip_schema = ['meta', 'sde']
    logging.debug('connecting to database')
    #: gdal.open gave a 0 table count
    connection = ogr.Open(connection_string)

    logging.debug('getting layer count')
    table_count = connection.GetLayerCount()

    logging.debug('found %s total tables for cache', table_count)
    CONNECTION_TABLE_CACHE.setdefault(connection_string, [])

    for table_index in range(table_count):
        qualified_layer = connection.GetLayerByIndex(table_index)
        table = None

        if qualified_layer:
            name = qualified_layer.GetName()
            logging.debug('qualified layer name: %s', name)

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
                else:
                    continue

                name = f'{schema_name}.{table}'

            logging.debug('found layer: %s', name)

            CONNECTION_TABLE_CACHE[connection_string].append(name)

    del qualified_layer
    connection = None


def _check_if_exists(connection_string, schema_name, table, agol_meta_map):
    """returns true or false if a table exists in the connections_string db
    connection_string: string of db to check
    schema_name: string schema name
    table: string table name
    returns: bool
    """
    logging.debug('checking cache')

    if schema_name in agol_meta_map and table in agol_meta_map[schema_name]:
        table, _ = agol_meta_map[schema_name][table].values()

    if connection_string in CONNECTION_TABLE_CACHE and len(CONNECTION_TABLE_CACHE[connection_string]) > 0:
        logging.debug('cache hit')

        return f'{schema_name}.{table}' in CONNECTION_TABLE_CACHE[connection_string]

    logging.debug('cache miss')
    _populate_table_cache(connection_string)

    found = False
    if f'{schema}.{table}' in CONNECTION_TABLE_CACHE[connection_string]:
        found = True

    return found


def _replace_data(schema_name, layer, fields, agol_meta_map, dry_run):
    """the insert logging for writing to the destination
    """
    cloud_db = config.format_ogr_connection(config.DBO_CONNECTION)
    internal_sgid = config.get_source_connection()

    internal_name = f'{schema_name}.{layer}'

    sql = f'SELECT objectid FROM "{schema_name}.{layer}"'

    if len(fields) > 0:
        #: escape reserved words?
        fields = [f'"{field}"' for field in fields]
        sql = f'SELECT {",".join(fields)} FROM "{schema_name}.{layer}"'

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
    else:
        logging.info('- skipping %s since it is no longer in the meta table', layer)

        return

    options.append('-nln')
    options.append(f'{layer}')

    pg_options = None
    try:
        pg_options = gdal.VectorTranslateOptions(options=options)
    except Exception:
        logging.fatal('- invalid options for %s', layer)
        return

    logging.info('- inserting %s into %s as %s', layer, schema_name, geometry_type)
    logging.debug('with %s', sql)

    if not dry_run:
        start_seconds = perf_counter()
        result = gdal.VectorTranslate(cloud_db, internal_sgid, options=pg_options)
        logging.debug('- completed in %s', utils.format_time(perf_counter() - start_seconds))

        del result

        logging.debug('make valid')

        qualified_layer = f'{schema_name}.{layer}'

        make_valid(qualified_layer)
        schema.update_schema_for(internal_name, qualified_layer)
        create_index(qualified_layer)


def import_data(if_not_exists, missing_only, dry_run):
    """imports data from sql to postgis
    if_not_exists: create new tables if the destination does not have it
    dry_run: do not modify the destination
    missing_only: only import missing tables
    """
    logging.info('importing tables missing from the source')

    cloud_db = config.format_ogr_connection(config.DBO_CONNECTION)
    internal_sgid = config.get_source_connection()

    tables = []
    if missing_only:
        source, destination = _get_table_sets()
        tables = destination - source

        table_count = len(tables)

        verb = 'are'
        noun = 'tables'
        if table_count == 1:
            verb = 'is'
            noun = 'table'

        logging.info('there %s %s %s in the source not in the destination', verb, table_count, noun)
        logging.debug(','.join(tables))

        if table_count == 0:
            return

    agol_meta_map = _get_table_meta()

    if missing_only:
        origin_table_name = []

        #: reverse lookup the table names
        for table in tables:
            schema_name, table_name = table.split('.')
            schema_name = schema_name.lower()
            table_name = table_name.lower()

            schema_items = agol_meta_map[schema_name]
            for origin_name in schema_items:
                if schema_items[origin_name]['title'] == table_name:
                    origin_table_name.append(f'{schema_name}.{origin_name}')
                    break

        if len(origin_table_name) > 0:
            tables = origin_table_name

    layer_schema_map = _get_tables_with_fields(internal_sgid, tables)

    for schema_name, layer, fields in layer_schema_map:
        if if_not_exists and _check_if_exists(cloud_db, schema_name, layer, agol_meta_map):
            logging.info('- skipping %s.%s already exists', schema_name, layer)

            continue

        _replace_data(schema_name, layer, fields, agol_meta_map, dry_run)


def _get_table_sets():
    """gets a set of each schema.tablename from the source and destination database to
    help figure out what is different between them
    """
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
    """get source tables with updated names
    get destination tables with original names
    drop the tables in the destination found in the difference between the two sets
    """

    logging.info('trimming tables that do not exist in the source')

    source, destination = _get_table_sets()
    items_to_trim = source - destination
    items_to_trim_count = len(items_to_trim)

    verb = 'are'
    noun = 'tables'
    if items_to_trim_count == 1:
        verb = 'is'
        noun = 'table'

    logging.info('there %s %s %s in the destination not in the source', verb, items_to_trim_count, noun)
    logging.debug(','.join(items_to_trim))

    if items_to_trim_count == 0:
        return

    clean_items = []
    for item in items_to_trim:
        schema_part, table = item.split('.')
        clean_items.append(f'{schema_part}."{table}"')

    sql = f'DROP TABLE {",".join(clean_items)}'
    logging.info('dropping %s', clean_items)

    if not dry_run:
        execute_sql(sql, config.DBO_CONNECTION)

    logging.info('finished')


def update(specific_tables, dry_run):
    """update specific tables in the destination
    specific_tables: a list of tables from the source without the schema
    dry_run: bool if insertion should actually happen
    """
    logging.info('updating tables %s', ','.join(specific_tables))

    internal_sgid = config.get_source_connection()

    if not specific_tables or len(specific_tables) == 0:
        logging.info(' no tables to import!')

        return

    layer_schema_map = _get_tables_with_fields(internal_sgid, specific_tables)

    if len(layer_schema_map) == 0:
        logging.info(' no matching table found!')

        return

    agol_meta_map = _get_table_meta()

    if len(specific_tables) != len(layer_schema_map):
        logging.warning(
            'input %s tables but only %s found. check your spelling', len(specific_tables), len(layer_schema_map)
        )

    for schema_name, layer, fields in layer_schema_map:
        _replace_data(schema_name, layer, fields, agol_meta_map, dry_run)


def read_last_check_date(gcp_bucket):
    """reads the last check date from the config file
    gcp_bucket: the bucket to find the file in
    """
    last_date_string = None
    last_checked = gcp_bucket.get_blob('.last_checked')

    if last_checked is None:
        return None

    last_date_string = last_checked.download_as_text()

    if last_date_string is None or len(last_date_string) < 1:
        return None

    return last_date_string


def update_last_check_date(gcp_bucket):
    """updates the last check date in the config file
    gcp_bucket: the bucket to find the file in
    """
    blob = gcp_bucket.get_blob('.last_checked')

    if blob is None:
        blob = storage.Blob('.last_checked', gcp_bucket)

    blob.upload_from_string(datetime.today().strftime('%Y-%m-%d'))


def get_tables_from_change_detection():
    """get changes from cambiador managed table
    """
    client = storage.Client()
    bucket = client.get_bucket('ut-dts-agrc-open-sgid-prod-data')

    last_checked = read_last_check_date(bucket)

    if last_checked is None:
        last_checked = datetime.today()
    else:
        last_checked = datetime.strptime(last_checked, '%Y-%m-%d')

    logging.info('Checking for changes since %s', last_checked)

    updated_tables = []
    with pyodbc.connect(config.get_source_connection()[6:]) as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT [TABLE_NAME] FROM [SGID].[META].[CHANGEDETECTION] WHERE [LAST_MODIFIED] >= ?", last_checked
        )
        rows = cursor.fetchall()

        #: table: SGID.ENVIRONMENT.DAQPermitCompApproval
        for table, in rows:
            table_parts = _get_schema_table_name_map(table)

            table_schema = table_parts['schema']
            table_name = table_parts['table_name']
            updated_tables.append(f'{table_schema}.{table_name}')

    update_last_check_date(bucket)

    return updated_tables


def make_valid(layer):
    """update invalid shapes in postgres
    """
    sql = f'UPDATE {layer} SET shape = ST_MakeValid(shape) WHERE ST_IsValid(shape) = false;'

    unfixable_layers = ['utilities.broadband_service']
    if layer in unfixable_layers:
        return

    try:
        execute_sql(sql, config.DBO_CONNECTION)
    except psycopg2.errors.UndefinedColumn:
        #: table doesn't have shape field
        pass


def create_index(layer):
    """ creates an index if available in the index map
    """
    if layer.lower() not in INDEXES:
        return

    logging.debug('- adding index')
    for sql in INDEXES[layer]:
        try:
            execute_sql(sql, config.DBO_CONNECTION)
        except Exception as ex:
            logging.warning('- failed running: %s%s', sql, ex)


def main():
    """Main entry point for program. Parse arguments and pass to sweeper modules.
    """
    args = docopt(__doc__, version='1.1.0')

    start_seconds = perf_counter()

    if args['enable']:
        enable_extensions()

        logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

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

            logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

            sys.exit()

        if args['read-only-user']:
            roles.create_read_only_user(config.SCHEMAS)

            logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

            sys.exit()

        if args['indexes']:
            for key, _ in INDEXES.items():
                create_index(key)

    if args['drop']:
        if args['schema']:
            name = args['--schemas']

            if name is None or name == 'all':
                schema.drop_schemas(config.SCHEMAS)

                logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

                sys.exit()

            name = name.lower()

            if name in config.SCHEMAS:
                schema.drop_schemas([name])

                logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

                sys.exit()

    if args['import']:
        import_data(args['--skip-if-exists'], args['--missing'], args['--dry-run'])

        logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

        sys.exit()

    if args['trim']:
        trim(args['--dry-run'])

        logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

        sys.exit()

    if args['update']:

        tables = args['--table']

        if args['--from-change-detection']:
            tables = get_tables_from_change_detection()

        update(tables, args['--dry-run'])

        logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

        sys.exit()

    if args['update-schema']:
        tables = args['--table']

        if len(tables) == 0:
            schema.update_schemas(_get_table_meta(), args['--dry-run'])
        else:
            agol_meta_map = _get_table_meta()

            for sgid_table in tables:
                schema_name, table_name = sgid_table.lower().split('.')
                pg_table = f'{schema_name}.{agol_meta_map[schema_name][table_name]["title"]}'

                schema.update_schema_for(sgid_table, pg_table, args['--dry-run'])

        logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

        sys.exit()

    logging.info('completed in %s', utils.format_time(perf_counter() - start_seconds))

    sys.exit()


if __name__ == '__main__':
    main()
