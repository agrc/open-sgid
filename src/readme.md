# cloudb CLI

A cli tool for taking spatial data from MSSQL and pushing it to PostGIS.

## installation

### python with conda

1. create a conda environment
   - `conda create -n cloudb`
   - `conda activate cloudb`
1. install the requirements
   - `conda install -c conda-forge gdal`
   - `pip install -e .`
   - for development `pip install -e ".[dev]"`
1. remove `.template` from `./src/cloudb/secrets/db/connection.template` and add the proper values
1. execute cli commands
   - `cloudb`

## usage

```sh
cloudb create admin-user
cloudb create schema [--schemas=<name>]
cloudb create read-only-user
cloudb import
cloudb sync
```

`cloudb sync` runs the production synchronization sequence: trim removed tables,
import missing data, and apply change-detection updates.

## Cloud Run Job

Production runs as the `cloudb` Cloud Run Job in `us-west3`. The Job uses one
task with three retries and is executed daily by Cloud Scheduler at midnight in
the `America/Denver` time zone.

Run the Job manually with:

```sh
gcloud run jobs execute cloudb --region=us-west3
```

Job executions and logs are available from the Cloud Run Jobs page and Cloud
Logging. The Scheduler service account needs `roles/run.invoker` on the Job.

## notes

- > pro tries to create tables that match the username. this is only important if you are creating data
- > a standard user should be able to run postgis functions. the only quirk might be needing to grant select on `spatial_ref_sys` and `geometry_columns`
- `CONVERT_TO_LINEAR` will remove curves. I don't believe we have any.
- `PROMOTE_TO_MULTI` for polygons that have multiple parts. This will upgrade them

### inserting new data

For data to synchronize to the Open SGID, the meta table needs a record with the following fields populated:

1. TABLENAME: The full qualified table name (e.g., SGID.ENVIRONMENT.NewDataset)
1. AGOL_PUBLISHED_NAME: The published name for PostgreSQL (e.g., "Utah New Dataset")
1. GEOMETRY_TYPE: The geometry type (POINT, POLYGON, POLYLINE, or STAND ALONE)

## links

- [gdal python docs](https://gdal.org/python/)
- [ogr2ogr docs](https://gdal.org/programs/ogr2ogr.html)
- [arcgis postgis requirements](https://pro.arcgis.com/en/pro-app/help/data/geodatabases/manage-postgresql/database-requirements-postgresql.htm)
- [postgresql tuning site](https://pgtune.leopard.in.ua/#/)
- [docker information](https://www.pgadmin.org/docs/pgadmin4/latest/container_deployment.html)
- [saving servers in pgadmin](https://www.pgadmin.org/docs/pgadmin4/development/import_export_servers.html#exporting-server)
