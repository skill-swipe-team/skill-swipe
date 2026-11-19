# skill-swipe

Minimal FastAPI service compatible with Python 3.10.4.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath ".env")) { Copy-Item .env.example .env }
```

Docker with Compose v2 is required for the local database. Start Docker Engine
(Docker Desktop on Windows) before running the service.

Configure the database in `.env`. This file is ignored by Git; only the
`.env.example` template is versioned. Its example credentials are for local
development only.

## Run

From the project root, start PostgreSQL and apply migrations in the background:

```powershell
docker compose up -d
docker compose ps -a
```

Compose starts Liquibase once PostgreSQL accepts TCP connections. Wait until
`postgres` is `healthy` and `migrate` shows `Exited (0)`. If the migration fails,
inspect `docker compose logs migrate`. Use `docker compose up` to follow both
services' logs in the foreground.

On first run, Compose pulls PostgreSQL and builds the Liquibase image if needed.
Use `docker compose up -d --build` after changing `migrations/Dockerfile`.
Changes to XML changelogs are picked up on the next run because Compose mounts
the `migrations/` directory into the container.

Start FastAPI on Windows with the virtual environment active:

```powershell
python -m uvicorn backend.main:app --reload
```

In VS Code, select `.venv\Scripts\python.exe` as the Python interpreter, then
choose **FastAPI: backend** in **Run and Debug** and press **F5**.
Open [Swagger UI](http://127.0.0.1:8000/docs) or check
[`GET /health`](http://127.0.0.1:8000/health) for `{"status":"ok"}`.

## Database

By default, the backend runs on the host and connects to PostgreSQL 17 from
Docker using the project-root `.env` file. No local PostgreSQL installation is
required. Database connection values are not hardcoded in Python or Compose.

- `POSTGRES_HOST`: the database host used by the backend.
- `POSTGRES_PORT`: the published Docker port used by the backend.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: database credentials shared by backend and Compose.
- Data is persisted in the `postgres_data` Docker volume at `/var/lib/postgresql/data`.

The template uses `127.0.0.1:5433` to avoid a conflict with a local PostgreSQL on
port `5432`. Compose binds the published port to loopback only. Process environment
variables take priority over `.env` values. Missing required settings cause an
explicit error rather than falling back to hardcoded credentials.

The backend creates an asyncpg connection pool, checks the database with
`SELECT 1` during startup, and closes the pool on shutdown. Startup fails if the
database cannot be reached. Routes can use `Depends(backend.database.get_connection)`
to acquire a connection from the pool. `/health` remains a service liveness check.

To connect to another database, set `DATABASE_URL` in `.env` or the backend process
environment before starting it. This optional variable overrides the individual
`POSTGRES_*` connection settings for the backend; Compose still uses `POSTGRES_*`.

```powershell
$env:DATABASE_URL = "postgresql://user:password@host:5432/database"
python -m uvicorn backend.main:app --reload
```

To return to the `.env` connection settings in PowerShell, remove the process override
(and remove `DATABASE_URL` from `.env` if it was added there):

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
```

### Connect from DBeaver

Create a PostgreSQL connection and use the settings from `.env`. With
`.env.example`, the host is `127.0.0.1`, the port is `5433`, and the
database, username, and password are all `skillswipe`. Select **Test Connection**.

Run these queries in the SQL editor to verify the connection and changelog:

```sql
SELECT current_database(), current_user, version();

SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'skillswipe';

SELECT id, tag, exectype
FROM public.databasechangelog
ORDER BY orderexecuted;
```

The schema query should return `skillswipe`, and the changelog should include
the tag `SSK-2`. The initial migration creates the schema only.

### Stop PostgreSQL

Stop the database without deleting its data:

```powershell
docker compose down
```

`docker compose down -v` deletes the database volume and all its data.
The `POSTGRES_*` settings initialize an empty volume only; changing them does not
reconfigure an existing database.

## Migrations

Migrations use Liquibase Community `5.0.4`, independently of Python and asyncpg.
The migration Docker image includes the pinned PostgreSQL JDBC driver `42.7.14`;
no local Java or Liquibase installation is required. The first build downloads
the Liquibase base image and JDBC driver.

Liquibase Community 5 uses [FSL-1.1-ALv2](https://github.com/liquibase/liquibase/blob/v5.0.4/LICENSE.txt).
Internal use for migrations of this application is free; the license restricts
competing commercial migration products and services.

- `migrations/master.yaml`: the ordered list of XML changelogs.
- `migrations/changelogs/ssk-2.xml`: tags the database as `SSK-2`, then creates the `skillswipe` schema.
- `migrations/Dockerfile`: the Liquibase image with the PostgreSQL JDBC driver.

The `migrate` service runs automatically with `docker compose up`. It connects to
the Docker database using the `POSTGRES_*` credentials from `.env` and exits
after applying pending changesets.
Liquibase stores `databasechangelog` and `databasechangeloglock` in `public`,
which already exists before the first migration creates `skillswipe`.
Repeating the update does not execute already applied changesets again.

Validate migrations and check pending changes:

```powershell
docker compose run --rm migrate validate
docker compose run --rm migrate status --verbose
```

For each new task, add an XML changelog to `migrations/changelogs/` and append its
`include` to `master.yaml`. Start with a dedicated `tagDatabase` changeset whose
tag matches the task ID, followed by changesets with inline `<sql>` and explicit
rollback SQL. Name changesets in the action-object style, for example
`create-skillswipe-schema`. Do not edit or rename already applied changesets.

If a database already ran the original `ssk-2.sql`, Liquibase treats the XML
schema changeset as new. `CREATE SCHEMA IF NOT EXISTS skillswipe` keeps the
existing schema and Liquibase records the XML changeset as executed. Rolling
back this changeset attempts to drop the schema even if it already existed.

Schema prefixes such as
`skillswipe.users` are optional for application tables. Liquibase uses `skillswipe`
as its default schema, and its
JDBC URL sets `currentSchema=skillswipe` for raw SQL. The backend pool also sets
`search_path=skillswipe`, so both migrations and application queries can use
unqualified names such as `users`.

The first migration creates `skillswipe` before later changesets create tables.
Liquibase's tracking tables remain explicitly in `public`, so bootstrapping does
not require the application schema to exist before the first changeset. For
example, a subsequent SQL migration can create a table without a schema prefix:

```sql
CREATE TABLE users (id bigint PRIMARY KEY);
```

The schema changeset's rollback uses `DROP SCHEMA skillswipe` without `CASCADE`,
so it cannot silently remove tables added later. The migration service targets
the Docker database; a backend `DATABASE_URL` override does not automatically
change the Liquibase JDBC connection URL.

## API

- Health check: [`GET /health`](http://127.0.0.1:8000/health)
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- OpenAPI schema: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Tests

```powershell
python -m pip install pytest httpx2 ruff
ruff check backend
ruff format --check backend
python -m pytest backend/tests/ -v
```

Unit tests mock the database pool and use temporary env files; they do not require
local credentials, a running PostgreSQL, or Docker. The separate `database-checks`
CI job starts a fresh PostgreSQL database with Compose, applies Liquibase
migrations, and checks the schema and changelog through the FastAPI connection pool.
