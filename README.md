# Asset Manager

**Branches:** `main` — MongoDB portfolio demo · `product` — sellable line on PostgreSQL (see below).

# Product branch — PostgreSQL

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL2) or Docker Engine.

## When do you need Postgres?

| You are doing | Start Postgres? |
| ------------- | --------------- |
| `pytest` / `npm run test` | **No** — tests use in-memory SQLite / no DB |
| Edit code only | **No** |
| `alembic upgrade head` | **Yes** |
| `uvicorn` on the host, or frontend hitting that API | **Yes** |
| pgAdmin / `psql` | **Yes** |
| Full stack via `docker-compose.product.yml` | Compose **starts** it for you |

Two start paths (both need repo-root `.env` from `.env.example`):

| Path | When | How the API finds the DB | Command |
| ---- | ---- | ------------------------ | ------- |
| **Local** (host `uvicorn` / Alembic / pgAdmin) | Daily product coding | `POSTGRES_URL` host = **`localhost`** | `docker compose -f docker-compose.product.yml up -d postgres` |
| **Compose / CI-style** (API container + DB) | Want the API in Docker too | Compose sets host = **`postgres`** | `docker compose -f docker-compose.product.yml up --build -d` |

There is no cloud Postgres in this repo yet. GitHub Actions pytest does **not** start Postgres; `compose-smoke` is the Mongo stack on `main`.

## 1. Environment

**Product branch:** copy `.env.example` → **`.env`** at the **repository root**. Used by Docker Compose, pgAdmin, and local `uvicorn` on this branch (`core/env.py` loads this file only).

Fill in `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `JWT_SECRET_KEY`. If you run the API with **`uvicorn` on the host** (not in Docker), also set `POSTGRES_URL` in the same file — host must be `localhost`, not `postgres`:

```text
POSTGRES_URL=postgresql+psycopg://<user>:<password>@localhost:<port>/<database>
```

`.env` is gitignored — never commit it.

**Master branch** uses **`backend/.env`** for local `uvicorn` (`MONGO_URI`, etc.) — that file is unrelated to `core/env.py`, which exists only on product.

## 2. Daily cheat sheet (product dev)

Copy-paste in order. All `docker compose` commands run from **repo root** (`~/assetManager`).

```bash
# 1) Start Postgres (Docker)
cd ~/assetManager
docker compose -f docker-compose.product.yml up -d postgres
docker compose -f docker-compose.product.yml ps    # postgres must be "healthy"

# 2) Run migrations (Alembic — must run from backend/)
cd ~/assetManager/backend
alembic upgrade head
alembic current

# 3) Optional: run API locally (not in Docker)
source venv/bin/activate
uvicorn main:app --reload
```

**Alembic from repo root** (if you are not in `backend/`):

```bash
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

Re-run `alembic upgrade head` from `backend/`.

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

`alembic.ini` lives in `backend/`. Run Alembic one of these ways:

| Where you are | Command                                       |
| ------------- | --------------------------------------------- |
| `backend/`    | `alembic upgrade head`                        |
| repo root     | `alembic -c backend/alembic.ini upgrade head` |

Check current revision:

```bash
cd ~/assetManager/backend
alembic current
```

After `upgrade head`, pgAdmin should show `users`, `stocks`, and `alembic_version`.

### Common errors

| Error                                           | Cause                                                | Fix                                                                  |
| ----------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------- |
| `No 'script_location' key found`                | Ran `alembic` outside `backend/` without `-c`        | `cd backend` or use `-c backend/alembic.ini`                         |
| `password authentication failed for user "..."` | Wrong DB instance (local PG on 5432) or stale volume | See **§3.D**; check `POSTGRES_URL` matches repo-root `.env`          |
| `POSTGRES_URL is required`                      | `.env` missing or empty                              | Fill repo-root `.env`; run from `backend/` so `core/env.py` loads it |

---

# Tech Stack (main / demo)

## Frontend

- React
- TypeScript
- Vite

## Backend

- Python FastAPI
- PyMongo
- Structured JSON logging
- Centralized API error handling
- Server-side pagination, filtering, search, and sorting

## Database

- MongoDB
- Indexes for email uniqueness, tea filtering, and text search

# Starting the Backend

Before entering virtual environment, the system Python will be used:

```bash
which python3
```

Output example: `/usr/bin/python3`

## Enter the backend virtual environment

```bash
cd ~/assetManager/backend/
source venv/bin/activate
```

Now the Python interpreter from the virtual environment will be used:

```bash
which python3
```

Output example: `/home/user/assetManager/backend/venv/bin/python3`

## Start the backend server

```bash
uvicorn main:app --reload
```

## Backend dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

Copy `.env.example` to `backend/.env` (or repo-root `.env` for Compose) and set `MONGO_URI` and `JWT_SECRET_KEY`.

## Run the backend with Docker Compose

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL2 on Windows) or Docker Engine on Linux.

From the **repository root**:

```bash
docker compose up --build -d
```

Check that the API and MongoDB are up:

```bash
curl http://localhost:8000/health   # liveness — process alive
curl http://localhost:8000/ready     # readiness — MongoDB reachable
```

Open `http://localhost:8000/docs` for the interactive API docs. The frontend still runs separately: `cd frontend && npm run dev` → `http://localhost:5173`.

Useful commands:

```bash
docker compose ps          # container status
docker compose logs api    # API logs
docker compose down        # stop; data kept in volume
docker compose down -v     # stop and delete Mongo data (reset DB)
```

Environment variables for Compose are set in `docker-compose.yml`. See `.env.example` for all supported variables and Atlas/local URI examples.

`pytest` does **not** require Docker (tests use an in-memory fake DB). Run tests the same way as below.

> **Note:** `mongo` publishes port `27017` to the host so you can connect with MongoDB Compass during local dev. That is fine for a resume demo on your machine. In production you would drop the host port mapping and require authentication.

## Tea API query examples

```bash
GET /api/tea?page=1&limit=20
GET /api/tea?genre=Oolong&sort_by=score&sort_direction=desc
GET /api/tea?search=Alishan
```

## Run backend tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

Run pytest from the `backend/` folder (not the repo root). `backend/pytest.ini` adds this directory to Python's path so `import main` works.

Auth tests cover tea mutations: `401` without cookie, `403` for non-admin (`user` / `guest`), `200` for admin.

## GitHub Actions CI

Workflow file: `.github/workflows/backend-ci.yml`

It runs on every push/PR to `main` or `master`:

**Job `test`**

1. Checkout code
2. Install Python 3.10
3. `pip install -r backend/requirements.txt`
4. `pytest -v` in `backend/`

**Job `compose-smoke`**

1. `docker compose up -d --build --wait`
2. `curl` `/health` and `/ready`
3. `docker compose down -v`

### One-time setup on GitHub

1. Push this repository to GitHub (if not already).
2. Open the repo on GitHub → **Actions** tab.
3. If prompted, click **Enable workflows**.
4. Push a commit or open a PR; you should see **Backend CI** running.
5. Green check = all tests passed.

No repository secrets are required for CI (tests use an in-memory fake DB, not Atlas).

Optional: add a status badge to `README.md`:

```markdown
![Backend CI](https://github.com/<your-username>/assetManager/actions/workflows/backend-ci.yml/badge.svg)
```

Replace `<your-username>` with your GitHub username or org.

## Exit the virtual environment

```bash
deactivate
```

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

---

### TODO

1. Add backend-starting command into bash: In `/backend/run.sh`, write `uvicorn main:app --reload`
2. Edit and delete functions in AssetList page
3. User: Admin

## Elements

- FastAPI - web framework
- uvicorn - ASGI server (run HTTP)
- Pydantic - 資料驗證
- PyMongo - DB client

## Note

- Python模組檔案裡，所有「在頂層定義的名字」都自動成為該模組的對外成員
  `router = APIRouter()` -> 建立一個物件、綁定到名字 router、放在 module 的最外層（不是在 function / class 裡）
- 看套件實際裝在哪裡: `python -m pip show fastapi`
- 看指令來源: `which uvicorn`
- 看venv中有哪些工具: `ls venv/bin/`
- 指定安裝套件在本虛擬環境: `python -m pip install {}`
