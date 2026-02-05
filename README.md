## Frontend

- React
- TypeScript
- Vite

## Backend

- Python FastAPI
- PyMongo

## DB

- MongoDB

## Enter backend virtual env

which python3
`/usr/bin/python3`

cd ~/assetManager/backend/
`source venv/bin/activate`.
To leave the venv: `deactivate`

which python3
`/home/jenny/assetManager/backend/venv/bin/python3`

## Start backend

`uvicorn main:app --reload`

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
