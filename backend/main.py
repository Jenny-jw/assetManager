from fastapi import FastAPI
from routes.tea import router as tea_router
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
app.include_router(tea_router)

@app.get("/")
def root():
    return {"messgae": "Hello FastAPI"}

@app.post("/echo")
def echo(data: dict):
    return {
        "received": data
    }