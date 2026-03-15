from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from routes.tea import router as tea_router
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",
]

app = FastAPI()
app.include_router(tea_router, prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)