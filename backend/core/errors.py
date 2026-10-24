import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "request_id": _request_id(request),
            }
        },
    )

def _safe_validation_errors(exc: RequestValidationError) -> list[dict]:
    errors = []
    for error in exc.errors():
        cleaned = {}
        for key, value in error.items():
            if key == "ctx" and isinstance(value, dict):
                cleaned[key] = {
                    ctx_key: str(ctx_value) if isinstance(ctx_value, BaseException) else ctx_value
                    for ctx_key, ctx_value in value.items()
                }
            else:
                cleaned[key] = value
        errors.append(cleaned)
    return errors

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = _safe_validation_errors(exc)
    return JSONResponse(
        status_code=422,
        content={
            "detail": details,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details,
                "request_id": _request_id(request),
            }
        },
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled application error",
        extra={"request_id": _request_id(request), "path": request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "request_id": _request_id(request),
            }
        },
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)