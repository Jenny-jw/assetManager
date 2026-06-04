from dotenv import load_dotenv
from fastapi import FastAPI
from routes.tea import router as tea_router
from routes.auth import router as auth_router
from core.security import router as security_router
from fastapi.middleware.cors import CORSMiddleware
from core.errors import register_exception_handlers
from core.indexes import ensure_indexes
from core.logging import RequestLoggingMiddleware, configure_logging
from contextlib import asynccontextmanager

load_dotenv()
configure_logging()

origins = [
    "http://localhost:5173",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_indexes()
    yield

app = FastAPI(title="Asset Manager API", version="0.1.0", lifespan=lifespan)
app.include_router(tea_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(security_router, prefix="/api")
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
register_exception_handlers(app)
