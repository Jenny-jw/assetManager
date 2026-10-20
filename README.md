# Asset Manager

**Branches:** `main` — MongoDB portfolio demo · `product` — sellable line on PostgreSQL (see below).

# Product branch — PostgreSQL

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL2) or Docker Engine.

**SaaS docs:** [concepts](docs/saas-concepts.md) (tenant, trial, edition vs status) · [ops](docs/saas-ops.md) (`.env`, practice compose, Alembic, manual `status` SQL).

## When do you need Postgres?

| You are doing                                       | Start Postgres?                             |
| --------------------------------------------------- | ------------------------------------------- |
| `pytest` / `npm run test`                           | **No** — tests use in-memory SQLite / no DB |
| Edit code only                                      | **No**                                      |
| `alembic upgrade head`                              | **Yes**                                     |
| `uvicorn` on the host, or frontend hitting that API | **Yes**                                     |
| pgAdmin / `psql`                                    | **Yes**                                     |
| Full stack via `docker-compose.product.yml`         | Compose **starts** it for you               |

Two start paths (both need repo-root `.env` from `.env.example`):

| Path                                           | When                       | How the API finds the DB              | Command                                                       |
| ---------------------------------------------- | -------------------------- | ------------------------------------- | ------------------------------------------------------------- |
| **Local** (host `uvicorn` / Alembic / pgAdmin) | Daily product coding       | `POSTGRES_URL` host = **`localhost`** | `docker compose -f docker-compose.product.yml up -d postgres` |
| **Compose / CI-style** (API container + DB)    | Want the API in Docker too | Compose sets host = **`postgres`**    | `docker compose -f docker-compose.product.yml up --build -d`  |

There is no cloud Postgres in this repo yet. GitHub Actions pytest uses in-memory SQLite (no Docker). On `product`, job `compose-smoke` starts `docker-compose.product.yml`, runs Alembic, then checks `/health` and `/ready`. The Mongo `compose-smoke` stays on `main` / `master`.

## 1. Environment

**Product branch:** copy `.env.example` → **`.env`** at the **repository root**. Used by Docker Compose, pgAdmin, and local `uvicorn` on this branch (`core/env.py` loads this file only).

Fill in `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `JWT_SECRET_KEY`. Optional: `TRIAL_DAYS` (new signups only; default 90). If you run the API with **`uvicorn` on the host** (not in Docker), also set `POSTGRES_URL` in the same file — host must be `localhost`, not `postgres`:

```text
POSTGRES_URL=postgresql+psycopg://<user>:<password>@localhost:<port>/<database>
```

`.env` is gitignored — never commit it.

Compose file on this branch is **`docker-compose.product.yml`**. Env is **repo-root `.env`** (`core/env.py`). Do not add `MONGO_URI` or `backend/.env` here.

## 2. Daily cheat sheet (product dev)

Copy-paste in order. All `docker compose` commands run from **repo root** (`~/assetManager`).

```bash
# 1) Start Postgres (Docker)
cd ~/assetManager
docker compose -f docker-compose.product.yml up -d postgres
docker compose -f docker-compose.product.yml ps    # postgres must be "healthy"

# 2) Activate venv, then run migrations (Alembic — from backend/)
cd ~/assetManager/backend
source venv/bin/activate
alembic upgrade head
alembic current

# 3) Optional: run API locally (not in Docker; venv already on)
uvicorn main:app --reload
```

`alembic` and `uvicorn` both live in `backend/venv`. Skip `source venv/bin/activate` only if you call the binaries directly (`./venv/bin/alembic`, `./venv/bin/uvicorn`).

**Alembic from repo root** (if you are not in `backend/`):

```bash
source backend/venv/bin/activate
alembic -c backend/alembic.ini upgrade head
```

## 3. Product local-dev SOP (details)

### A. Start DB only (most common)

Use when you run `uvicorn` on the host or only need pgAdmin.

```bash
cd ~/assetManager
docker compose -f docker-compose.product.yml up -d postgres
docker compose -f docker-compose.product.yml ps
```

Expected: `postgres` status is `Up ... (healthy)`.

### B. Start DB + API in Docker

Use when you want the full stack in containers (no local `uvicorn`).

```bash
cd ~/assetManager
docker compose -f docker-compose.product.yml up --build -d
docker compose -f docker-compose.product.yml ps
curl http://localhost:8000/ready
```

Containers healthy does **not** mean tables exist. The API image does not run Alembic. After `up`, still migrate (`alembic upgrade head` on the host, or `docker compose -f docker-compose.product.yml exec api alembic upgrade head`). Details: [docs/saas-ops.md](docs/saas-ops.md) §3.B.

### C. Stop services

```bash
cd ~/assetManager
docker compose -f docker-compose.product.yml down
```

Reset DB data (destructive — wipes volume):

```bash
docker compose -f docker-compose.product.yml down -v
```

### D. Port 5432 conflict (local PostgreSQL vs Docker)

If `alembic` or pgAdmin fails with `password authentication failed for user "assetmanager"`, you are often connecting to **local PostgreSQL** (roles: `jenny`, `postgres`) instead of **Docker PostgreSQL** (role: `assetmanager`).

`alembic` uses `POSTGRES_URL` → `localhost:5432` on your machine. That is **not** the same as `docker compose exec postgres psql ...` (which talks to DB **inside** the container).

**Step 1 — stop local PostgreSQL**

```bash
sudo service postgresql stop
# or: sudo systemctl stop postgresql
```

**Step 2 — confirm who owns port 5432**

```bash
ss -tlnp | grep 5432
```

- `docker-proxy` / `0.0.0.0:5432` → Docker (good for Alembic via localhost)
- `postgres` on `127.0.0.1:5432` → local PG still running (Alembic will fail)

**Step 3 — verify Docker DB**

```bash
cd ~/assetManager
set -a && source .env && set +a
docker compose -f docker-compose.product.yml exec postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;"
```

Replace `assetmanager` / `assetmanager_product` with your repo-root `.env` values if different.

**Step 4 — verify from host (same path Alembic uses)**

```bash
PGPASSWORD=assetmanager psql -h 127.0.0.1 -p 5432 -U assetmanager -d assetmanager_product -c "SELECT 1;"
```

If Step 3 works but Step 4 fails → port conflict; local PG is still on 5432.

**Stable fix (recommended on WSL): use port 5433 for Docker**

In repo-root `.env`:

```text
POSTGRES_PORT=5433
POSTGRES_URL=postgresql+psycopg://assetmanager:assetmanager@localhost:5433/assetmanager_product
```

Then:

```bash
cd ~/assetManager
docker compose -f docker-compose.product.yml down
docker compose -f docker-compose.product.yml up -d postgres
```

From `backend/`, activate the venv (or use `./venv/bin/alembic`) and re-run `alembic upgrade head`.

**If credentials changed after first `docker compose up`**, reset the volume (deletes DB data):

```bash
docker compose -f docker-compose.product.yml down -v
docker compose -f docker-compose.product.yml up -d postgres
```

## 4. pgAdmin 4 — connect to local Postgres

Start the DB first (`up -d postgres`). pgAdmin is a GUI client (like Compass for Mongo); credentials come from **your local `.env`**, not from this repo.

1. Open **pgAdmin 4** → **Servers** → right-click → **Register** → **Server…**
2. **General** → **Name:** any label (e.g. `local product`)
3. **Connection** — use the same values you set in `.env`:

   | Field                | Source                                         |
   | -------------------- | ---------------------------------------------- |
   | Host                 | `localhost` (Docker maps port to your machine) |
   | Port                 | `POSTGRES_PORT` (default `5432`)               |
   | Maintenance database | `POSTGRES_DB`                                  |
   | Username             | `POSTGRES_USER`                                |
   | Password             | `POSTGRES_PASSWORD`                            |

4. **Save** → **Databases →** your `POSTGRES_DB` name.

**Query Tool:** right-click the database → **Query Tool** → `SELECT 1;`

If connection fails: `docker compose -f docker-compose.product.yml ps` — `postgres` should be healthy.

## 5. Database migrations (Alembic)

`alembic.ini` lives in `backend/`. Alembic is installed in `backend/venv` — activate that venv first, or invoke `./venv/bin/alembic`. Then run one of:

| Where you are | Command                                       |
| ------------- | --------------------------------------------- |
| `backend/`    | `alembic upgrade head`                        |
| repo root     | `alembic -c backend/alembic.ini upgrade head` |

Check current revision:

```bash
cd ~/assetManager/backend
source venv/bin/activate
alembic current
```

After `upgrade head`, pgAdmin should show `users`, `stocks`, and `alembic_version`.

### Common errors

| Error                                           | Cause                                                | Fix                                                                  |
| ----------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------- |
| `alembic: command not found`                    | venv not activated (Alembic is not on system PATH)   | `cd backend && source venv/bin/activate`, or `./venv/bin/alembic`    |
| `No 'script_location' key found`                | Ran `alembic` outside `backend/` without `-c`        | `cd backend` or use `-c backend/alembic.ini`                         |
| `password authentication failed for user "..."` | Wrong DB instance (local PG on 5432) or stale volume | See **§3.D**; check `POSTGRES_URL` matches repo-root `.env`          |
| `POSTGRES_URL is required`                      | `.env` missing or empty                              | Fill repo-root `.env`; run from `backend/` so `core/env.py` loads it |

---

# Tech stack (this branch)

**Frontend:** React 19, TypeScript, Vite, Tailwind, i18n (`zh-TW` \| `en`)

**Backend:** FastAPI, SQLAlchemy, Alembic, JWT cookie auth (`owner` only)

**Database:** PostgreSQL (`POSTGRES_URL`). Shared SaaS with `tenant_id` (ADR 005).

`main` / `master` is a separate Mongo portfolio demo. Do not merge whole `product` ↔ `main`.

# Backend venv

```bash
cd ~/assetManager/backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

`which python3` should show `.../backend/venv/bin/python3`. Then migrate and run (Postgres already healthy — §2):

```bash
alembic upgrade head
uvicorn main:app --reload
```

API docs: `http://localhost:8000/docs`. Frontend is separate (`npm run dev` below). Leave the venv with `deactivate`.

## Stock API (owner cookie required)

```bash
GET /api/stock?page=1&limit=20
GET /api/stock?genre=Oolong&sort_by=score&sort_direction=desc
GET /api/stock?search=Alishan
GET /api/stock/summary
```

## Run backend tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

Run from `backend/` (`pytest.ini` puts that directory on `PYTHONPATH`). Pytest uses in-memory SQLite; do not start Postgres. Tests are `owner` + PostgreSQL domain.

## GitHub Actions CI

Workflow files: `.github/workflows/backend-ci.yml`, `.github/workflows/frontend-ci.yml`

They run on every push/PR to `product`:

**Job `test`** (backend)

1. Checkout code
2. Install Python 3.10
3. `pip install -r backend/requirements.txt`
4. `pytest -v` in `backend/` (in-memory SQLite; Postgres is not required)

**Job `compose-smoke`** (backend)

1. Write a throwaway root `.env` (CI dummy `POSTGRES_*` / `JWT_*`; never commit)
2. `docker compose -f docker-compose.product.yml up -d --build --wait`
3. `alembic upgrade head` inside the `api` container
4. `curl` `/health` and `/ready`
5. `docker compose -f docker-compose.product.yml down -v`

**Frontend CI:** Node 24; `npm ci`, lint, Vitest, production build.

### One-time setup on GitHub

1. Push this repository to GitHub (if not already).
2. Open the repo on GitHub → **Actions** tab.
3. If prompted, click **Enable workflows**.
4. Push a commit or open a PR targeting `product`; you should see **Backend CI** and **Frontend CI** running.
5. Green check = all tests passed.

No repository secrets are required for CI.

Optional: add a status badge to `README.md`:

```markdown
![Backend CI](https://github.com/<your-username>/assetManager/actions/workflows/backend-ci.yml/badge.svg)
```

Replace `<your-username>` with your GitHub username or org.

# Starting the Frontend

```bash
cd ~/assetManager/frontend/
npm run dev
```

## Run frontend tests

```bash
cd frontend
npm run test
```

Tests live in `frontend/tests/` (e.g. `tests/routes/ProtectedRoute.test.tsx`). Use `@/` imports for `src/` modules.
