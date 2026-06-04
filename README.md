# Tech Stack

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

Copy `backend/.env.example` to `backend/.env` and set `MONGO_URI` and `JWT_SECRET_KEY`.

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

1. Checkout code
2. Install Python 3.10
3. `pip install -r backend/requirements.txt`
4. `pytest -v` in `backend/`

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

## Frontend Pages Design

### Dashboard

- Path: `/`
- Total asset
- Assets added recently
- Recent activities

### Asset List

- Path: `/assets`
- List out all the assets, such as, Name, Type, Owner, Value
- Functions: search, filter, sort

### Aseet Detail

- Path: `/assets/:id`
- Present single asset details

### Create Asset

- Path: `/assets/new`
- Create an asset: Name, Origin, HarvestTime, Cost, Price

### Edit Asset

- Path: `/assets/:id/edit`

### Login (if there's user)

- Path: `/login`

