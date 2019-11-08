# cloudb

A cli tool for taking data from MSSQL and pushing it to PostGIS.

## installation

1. create a python conda environment
   - `conda create --name cloudb python=3.7`
1. activate the environment
   - `activate cloudb`
1. install requirements
   - `conda install psycopg2 docopt gdal colorama && pip install python-dotenv`
1. fill out the `config.py` variables
1. fill out the `.env` variables
1. navigate to the `src` directory of this project
1. execute cli commands
   - `python -m cloudb ...`

## usage

```sh
cloudb create schema [--schemas=<name>]
cloudb create admin-user
cloudb create db [--name=<name>]
cloudb import
```

## connect to your db

1. start the docker container
   - `docker-compose up -d`
1. browse to the pgAdmin [website](https://localhost:8080)
1. log in with the credentials in `.env`

## notes

- > pro tries to create tables that match the username. this is only important if you are creating data
- > a standard user should be able to run postgis functions. the only quirk might be needing to grant select on `spatial_ref_sys` and `geometry_columns`
- i had a hard time getting the geometry type so everything is importing as geometry
  - `CONVERT_TO_LINEAR` will remove curves. I don't believe we have any.
  - `PROMOTE_TO_MULTI` for polygons that have multiple parts. This will upgrade them

## links

- [gdal python docs](https://gdal.org/python/)
- [ogr2ogr docs](https://gdal.org/programs/ogr2ogr.html)
- [arcgis postgis requirements](https://pro.arcgis.com/en/pro-app/help/data/geodatabases/manage-postgresql/database-requirements-postgresql.htm)
- [postgresql tuning site](https://pgtune.leopard.in.ua/#/)
- [docker information](https://www.pgadmin.org/docs/pgadmin4/latest/container_deployment.html)
- [saving servers in pgadmin](https://www.pgadmin.org/docs/pgadmin4/development/import_export_servers.html#exporting-server)
