#!/usr/bin/env python
# * coding: utf8 *
'''
config.py
A module that holds configuration items
'''
from textwrap import dedent
from dotenv import load_dotenv

import os

load_dotenv()

SCHEMAS = [
    'bioscience', 'boundaries', 'cadastre', 'climate', 'demographic', 'economy', 'elevation', 'energy', 'environment', 'farming', 'geoscience', 'health',
    'history', 'indices', 'location', 'planning', 'political', 'raster', 'recreation', 'society', 'transportation', 'utilities', 'water'
]

DB = 'cloud'

DBO = 'postgres'

ADMIN = {'name': 'dba', 'password': os.getenv('CLOUDB_ADMIN_PASSWORD')}

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

MERCATOR = dedent(
    '''PROJCS["WGS 84 / Pseudo-Mercator",
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.0174532925199433,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4326"]],
    PROJECTION["Mercator_1SP"],
    PARAMETER["central_meridian",0],
    PARAMETER["scale_factor",1],
    PARAMETER["false_easting",0],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    AXIS["X",EAST],
    AXIS["Y",NORTH],
    EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs"],
    AUTHORITY["EPSG","3857"]]'''
)

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
    #: local_sgid = 'MSSQL:driver=ODBC Driver 17 for SQL Server;server=(local);database=UDEQ;trusted_connection=yes;'
    return f"MSSQL:driver=ODBC Driver 17 for SQL Server;server={SRC_CONNECTION['host']};database={SRC_CONNECTION['database']};trusted_connection=no;UID={SRC_CONNECTION['user']};PWD={SRC_CONNECTION['password']};"
