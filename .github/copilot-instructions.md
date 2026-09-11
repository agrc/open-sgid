# Open SGID agent instructions

## Repository overview

Open SGID is a small Python `src`-layout package. The `cloudb` CLI synchronizes spatial data from the internal MSSQL SGID into the public PostgreSQL/PostGIS Open SGID mirror. GDAL/OGR performs the spatial transfer; PostgreSQL 14 and PostGIS 3.6 are the documented target database versions. Production runs as a single-task Cloud Run Job invoked by Cloud Scheduler.

Important runtime dependencies are GDAL 3.x, Microsoft ODBC Driver 17 for SQL Server, UnixODBC, `pyodbc`, `psycopg2`, and Google Cloud Storage. The package has no lockfile and does not declare a Python version. Do not assume a database, MSSQL source, Cloud SQL credentials, GCP access, or Secret Manager access is available in a development checkout.

## Layout and ownership

- `src/cloudb/main.py`: CLI grammar and synchronization logic: import, update, trim, schema updates, change detection, GDAL setup, and geometry repair. It imports GDAL, ODBC, PostgreSQL, and Google Cloud libraries at module load.
- `src/cloudb/config.py`: loads JSON secrets from `/secrets/db/connection` in Cloud Run or `src/cloudb/secrets/db/connection` locally; defines schemas, connections, exclusions, and EPSG:26912 projection.
- `src/cloudb/schema.py` and `src/cloudb/roles.py`: database schema/type and role/privilege operations.
- `src/cloudb/index.py`: hardcoded index definitions; `tests/test_index.py` checks the count of index groups.
- `src/cloudb/__init__.py`: SQL helper, logging, and connection-table cache. `src/cloudb/utils.py`: small utility helpers.
- `setup.py`: package metadata, dependencies, `cloudb = cloudb.main:main` entry point, and `dev` extras. `pyproject.toml`: Ruff/Black line length 120 and pytest configuration.
- `Dockerfile`: production image based on `ghcr.io/osgeo/gdal:ubuntu-full-3.12.4`; installs Python, UnixODBC, Microsoft ODBC Driver 17, then runs `cloudb sync`.
- `src/readme.md`: local installation and operational CLI documentation. `readme.md`: Open SGID overview, terms of service, and database version information. `AI_ATTESTATION.md`: AI-use attestation. `CHANGELOG.md`: auto-generated release history; never edit it manually.

Root-level support files include `.dockerignore`, `.editorconfig`, `.gitignore`, `.gitattributes`, `cov.xml`, `LICENSE`, and `bh-set-envvars.sh`. The shell script only prepares architecture/compiler environment variables; it is not the build or test entry point.

## Setup and validation

Assume the user has already created a Conda environment named `cloudb` for this project. Use that environment for all commands. If it is not available, ask the user whether they would like you to set it up before attempting environment creation; do not create a different environment automatically.

```sh
conda activate cloudb
python -m pip install -e ".[dev]"
```

Always install the `dev` extra before running the full test command. The corrected development-install syntax is `pip install -e ".[dev]"`; do not use the malformed example in `src/readme.md`. On macOS, the editable install may require native GDAL first (for example, `brew install gdal`, or the equivalent Conda package) so `gdal-config` is available. This prerequisite was observed in the current environment: Python 3.14.7/pip 26.2.1 are installed, but `python -m pip install -e ".[dev]"` fails because `gdal-config` is missing. Do not claim tests passed until installation succeeds.

After installation, run:

```sh
pytest
```

`pytest` includes Ruff, branch coverage, `cov.xml` generation, and `pytest-instafail` through `pyproject.toml`. The equivalent explicit command is:

```sh
pytest --ruff --cov-branch --cov=cloudb --cov-report term --cov-report xml:cov.xml --instafail
```

For a lint-only check, run `ruff check .`. For a dependency-free syntax check, run `python -m compileall -q src tests`; this passed in the current environment. VS Code enables pytest and adds `--no-cov` for editor runs. There is no separate build script or standalone CI test job. Keep generated coverage changes (`cov.xml`, `.coverage`) out of unrelated changes unless intentionally updating coverage.

Do not run database-changing CLI commands as validation. They require a real JSON connection file and can overwrite or alter production-like data. The CLI supports `--dry-run` for applicable import/update/trim/schema operations, but even dry runs require appropriate connections. Never print, commit, or copy credentials from either the local secret file or the root README.

The container path is production-oriented and requires Docker, network access, GCP credentials for deployment, and database secrets. Build locally with `docker build -t cloudb .`; do not push or deploy from an agent task unless explicitly requested. The image command is `cloudb sync`.

## CI/CD and change discipline

- `.github/workflows/push.yml` runs on pushes to `dev` and `main` and invokes `agrc/release-composite-action@v1` to create releases/prereleases. It does not run pytest or Ruff directly.
- `.github/workflows/release.yml` deploys published non-prereleases: Docker/Buildx, Artifact Registry, Google OIDC, Cloud Run in `us-west3`, Secret Manager mount `/secrets/db/connection`, and a daily Mountain Time Cloud Scheduler job. It needs the `prod` environment and configured GCP service accounts, project, VPC, registry, and secret infrastructure.
- `.github/dependabot.yml` updates pip, GitHub Actions, and Docker dependencies quarterly with grouped updates and cooldowns.

Changes affecting imports, SQL, schemas, roles, geometry, change detection, or scheduling have integration risk not covered by the single unit test. Prefer small, testable changes and add focused tests that do not require external databases. Preserve the existing `src` layout, 120-character formatting convention, and public CLI/API behavior unless the task explicitly changes them. Review SQL identifier handling, transaction boundaries, checkpoint updates, and HTTP failure status carefully because these are operationally significant.

Do not edit `CHANGELOG.md`. It is auto-generated by the release process; record user-facing changes in the appropriate source documentation or release metadata instead.

Before finishing, run the strongest available checks in this order: install the tests extra, `pytest`, `ruff check .` if needed for diagnosis, and `python -m compileall -q src tests`. Inspect the diff and ensure no secrets, generated artifacts, or unrelated files changed. Trust these instructions and use repository search only when a stated detail is incomplete or proves inaccurate.
