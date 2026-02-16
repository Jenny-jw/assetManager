from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from routes.tea import router as tea_router

app = FastAPI()
app.include_router(tea_router)