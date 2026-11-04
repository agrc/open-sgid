"""
config.py
A module that holds configuration items
"""
from textwrap import dedent

from .config_loader import ConfigurationError, load_connection_secrets

__all__ = ["ConfigurationError"]

secrets = load_connection_secrets()
GOOGLE_CHAT_WEBHOOK = secrets.get("googleChatWebhookUrl")

SCHEMAS = [
    "bioscience",
    "boundaries",
    "cadastre",
    "climate",
    "demographic",
    "economy",
    "elevation",
    "energy",
    "environment",
    "farming",
    "geoscience",
    "health",
    "history",
    "indices",
    "location",
    "planning",
    "political",
    "raster",
    "recreation",
    "society",
    "transportation",
    "utilities",
    "water",
]

EXCLUDE_SCHEMAS = ["sde", "meta"]
EXCLUDE_FIELDS = ["objectid", "fid", "gdb_geomattr_data"]

DB = "opensgid"

DBO = "postgres"

ADMIN = {
    "name": "dba",
    "password": secrets["adminPassword"],
}

PUBLIC = {
    "name": "sgid_viewer",
    "password": secrets["publicPassword"],
}

SRC_CONNECTION = {
    "host": secrets["srcHost"],
    "database": "SGID",
    "user": "internal",
    "password": secrets["srcPassword"],
}

DBO_CONNECTION = {
    "host": secrets["host"],
    "database": DB,
    "user": DBO,
    "password": secrets["pgPassword"],
}

DBA_CONNECTION = {
    "host": secrets["host"],
    "database": DB,
    "user": ADMIN["name"],
    "password": ADMIN["password"],
}

UTM = dedent(
    """PROJCS["NAD83 / UTM zone 12N",
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
    AXIS["Northing",NORTH]]"""
)


def format_ogr_connection(connection):
    """a method to format a connection string for ogr usage"""
    return (
        f"PG:host={connection['host']} "
        f"port=5432 user='{connection['user']}' "
        f"password='{connection['password']}' "
        f"dbname='{connection['database']}'"
    )


def get_source_connection():
    """a method to format the sql server source data connection string"""
    return (
        "MSSQL:driver=ODBC Driver 18 for SQL Server;"
        "TrustServerCertificate=yes;"
        f"server={SRC_CONNECTION['host']};"
        f"database={SRC_CONNECTION['database']};"
        f"UID={SRC_CONNECTION['user']};"
        f"PWD={SRC_CONNECTION['password']};"
        "trusted_connection=no;"
    )
