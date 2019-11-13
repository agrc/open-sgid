#!/usr/bin/env python
# * coding: utf8 *
'''
config.py
A module that holds configuration items
'''
import os
from textwrap import dedent

from dotenv import load_dotenv

load_dotenv()

SCHEMAS = [
    'bioscience', 'boundaries', 'cadastre', 'climate', 'demographic', 'economy', 'elevation', 'energy', 'environment', 'farming', 'geoscience', 'health',
    'history', 'indices', 'location', 'planning', 'political', 'raster', 'recreation', 'society', 'transportation', 'utilities', 'water'
]

EXCLUDE_SCHEMAS = ['sde', 'meta']
EXCLUDE_FIELDS = ['objectid', 'fid', 'globalid', 'gdb_geomattr_data']

DB = 'cloud'

DBO = 'postgres'

ADMIN = {
    'name': 'dba',
    'password': os.getenv('CLOUDB_ADMIN_PASSWORD'),
}

PUBLIC = {
    'name': 'sgid_viewer',
    'password': os.getenv('CLOUDB_PUBLIC_PASSWORD'),
}

SRC_CONNECTION = {
    'host': os.getenv('CLOUDB_SRC_HOST'),
    'database': 'SGID',
    'user': 'internal',
    'password': os.getenv('CLOUDB_SRC_PASSWORD'),
}

DBO_CONNECTION = {
    'host': os.getenv('CLOUDB_HOST'),
    'database': DB,
    'user': DBO,
    'password': os.getenv('CLOUDB_PG_PASSWORD'),
}

DBA_CONNECTION = {
    'host': os.getenv('CLOUDB_HOST'),
    'database': DB,
    'user': ADMIN['name'],
    'password': ADMIN['password'],
}

UTM = dedent(
    '''PROJCS["NAD83 / UTM zone 12N",
    GEOGCS["NAD83",
        DATUM["North_American_Datum_1983",
            SPHEROID["GRS 1980",6378137,298.257222101,
                AUTHORITY["EPSG","7019"]],
            AUTHORITY["EPSG","6269"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.01745329251994328,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4269"]],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    PROJECTION["Transverse_Mercator"],
    PARAMETER["latitude_of_origin",0],
    PARAMETER["central_meridian",-111],
    PARAMETER["scale_factor",0.9996],
    PARAMETER["false_easting",500000],
    PARAMETER["false_northing",0],
        AUTHORITY["EPSG","26912"],
    AXIS["Easting",EAST],
    AXIS["Northing",NORTH]]'''
)


def format_ogr_connection(connection):
    return f"PG:host={connection['host']} port=5432 user='{connection['user']}' password='{connection['password']}' dbname='{connection['database']}'"


def get_source_connection():
    return (
        'MSSQL:driver=ODBC Driver 17 for SQL Server;'
        f"server={SRC_CONNECTION['host']};"
        f"database={SRC_CONNECTION['database']};"
        f"UID={SRC_CONNECTION['user']};"
        f"PWD={SRC_CONNECTION['password']};"
        'trusted_connection=no;'
    )
