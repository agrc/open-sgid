# cloudb CLI

A cli tool for taking data from MSSQL and pushing it to PostGIS.

## installation

### python

1. create a python 3 virtual environment
   - `python -m venv .env`
1. pip install the module
   - `pip install .`
   - for development `pip install . -e ."[tests]"

### terraform

1. install terraform cli
1. create a service account with `project > editor` privileges
1. place the service worker file in the `terraform` folder named as `terraform-sa.json`
1. initialize terraform
   - `cd src/terraform`
   - `terraform init`
1. create the database
   - `terraform apply`
   - terraform will output the `postgres` user password, the cloud db host ip, and the default database name. Use those values to fill out the `src/cloudb/.env` file

### python again

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
