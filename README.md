# Tech Stack

## Frontend

- React
- TypeScript
- Vite

## Backend

- Python FastAPI
- PyMongo

## Database

- MongoDB

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

## Exit the virtual environment

```bash
deactivate
```

## Start the backend server

```bash
uvicorn main:app --reload
```

<hr>

### TODO

1. Add backend-starting command into bash: In `/backend/run.sh`, write `uvicorn main:app --reload`

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
