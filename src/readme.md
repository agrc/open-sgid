# cloudb CLI

A cli tool for taking data from MSSQL and pushing it to PostGIS.

## installation

### python

1. create a conda environment
   - `conda create -n cloudb`
   - `conda activate cloudb`
1. install the requirements
   - `conda install -c conda-forge gdal`
   - `pip install -e .`
   - for development `pip install . -e ."[tests]"
1. fill out the `.env` variables
1. execute cli commands
   - `cloudb`

## usage

```sh
cloudb create admin-user
cloudb create schema [--schemas=<name>]
cloudb create read-only-user
cloudb import
```

## notes

- > pro tries to create tables that match the username. this is only important if you are creating data
- > a standard user should be able to run postgis functions. the only quirk might be needing to grant select on `spatial_ref_sys` and `geometry_columns`
- `CONVERT_TO_LINEAR` will remove curves. I don't believe we have any.
- `PROMOTE_TO_MULTI` for polygons that have multiple parts. This will upgrade them

## links

- [gdal python docs](https://gdal.org/python/)
- [ogr2ogr docs](https://gdal.org/programs/ogr2ogr.html)
- [arcgis postgis requirements](https://pro.arcgis.com/en/pro-app/help/data/geodatabases/manage-postgresql/database-requirements-postgresql.htm)
- [postgresql tuning site](https://pgtune.leopard.in.ua/#/)
- [docker information](https://www.pgadmin.org/docs/pgadmin4/latest/container_deployment.html)
- [saving servers in pgadmin](https://www.pgadmin.org/docs/pgadmin4/development/import_export_servers.html#exporting-server)
