from __future__ import annotations

from enum import Enum
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class ErrorCode(str, Enum):
    module_disabled = "module_disabled"
    capability_disabled = "capability_disabled"
    role_not_enabled = "role_not_enabled"
    forbidden = "forbidden"
    tenant_suspended = "tenant_suspended"
    trial_expired = "trial_expired"
    tenant_required = "tenant_required"
    tenant_not_found = "tenant_not_found"
    not_authenticated = "not_authenticated"
    invalid_token = "invalid_token"
    invalid_token_payload = "invalid_token_payload"
    invalid_credentials = "invalid_credentials"
    user_not_found = "user_not_found"
    slug_taken = "slug_taken"
    duplicate_registration = "duplicate_registration"
    signup_disabled = "signup_disabled"
    invalid_stock_id = "invalid_stock_id"
    stock_not_found = "stock_not_found"
    stock_not_orderable = "stock_not_orderable"
    invalid_order_id = "invalid_order_id"
    order_not_found = "order_not_found"
    order_not_pending = "order_not_pending"
    order_has_no_items = "order_has_no_items"
    insufficient_stock = "insufficient_stock"
    no_fields_to_update = "no_fields_to_update"
    invalid_weight = "invalid_weight"
    validation_error = "validation_error"
    internal_server_error = "internal_server_error"
    http_error = "http_error"

ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.module_disabled: "This module is not enabled for the current tenant.",
    ErrorCode.capability_disabled: "This action is not available for the current role.",
    ErrorCode.role_not_enabled: "This role is not enabled for the current tenant.",
    ErrorCode.forbidden: "Forbidden",
    ErrorCode.tenant_suspended: "This tenant is suspended.",
    ErrorCode.trial_expired: "This trial has expired.",
    ErrorCode.tenant_required: "A tenant is required for this request.",
    ErrorCode.tenant_not_found: "Tenant not found",
    ErrorCode.not_authenticated: "Not authenticated",
    ErrorCode.invalid_token: "Invalid or expired token",
    ErrorCode.invalid_token_payload: "Invalid token payload",
    ErrorCode.invalid_credentials: "Invalid username or password",
    ErrorCode.user_not_found: "User not found",
    ErrorCode.slug_taken: "Tenant slug already registered",
    ErrorCode.duplicate_registration: "Username, email, or tenant slug already registered",
    ErrorCode.signup_disabled: "Signup is disabled.",
    ErrorCode.invalid_stock_id: "Invalid stock id",
    ErrorCode.stock_not_found: "Stock not found",
    ErrorCode.stock_not_orderable: "Stock is missing price or package weight and cannot be ordered",
    ErrorCode.invalid_order_id: "Invalid order id",
    ErrorCode.order_not_found: "Order not found",
    ErrorCode.order_not_pending: "Order is not pending approval",
    ErrorCode.order_has_no_items: "Order has no items",
    ErrorCode.insufficient_stock: "Insufficient stock for one or more items",
    ErrorCode.no_fields_to_update: "No fields to update",
    ErrorCode.invalid_weight: "Package weight is invalid for this edition.",
    ErrorCode.validation_error: "Request validation failed",
    ErrorCode.internal_server_error: "An unexpected error occurred",
    ErrorCode.http_error: "Request failed",
}

class ApiError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: ErrorCode,
        *,
        message: str | None = None,
    ) -> None:
        self.error_code = code.value
        self.error_message = message or ERROR_MESSAGES[code]
        super().__init__(status_code=status_code, detail=self.error_code)

def api_error(
    status_code: int,
    code: ErrorCode,
    *,
    message: str | None = None,
) -> ApiError:
    return ApiError(status_code, code, message=message)

def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)

def _known_code(value: object) -> ErrorCode | None:
    if not isinstance(value, str):
        return None
    try:
        return ErrorCode(value)
    except ValueError:
        return None

def error_body(
    *,
    code: ErrorCode | str,
    message: str,
    request_id: str | None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    code_value = code.value if isinstance(code, ErrorCode) else code
    error: dict[str, object] = {
        "code": code_value,
        "message": message,
        "request_id": request_id,
    }
    if extra:
        error.update(extra)
    return {"detail": code_value, "error": error}

def _http_error_fields(exc: HTTPException) -> tuple[str, str]:
    if isinstance(exc, ApiError):
        return exc.error_code, exc.error_message
    known = _known_code(exc.detail)
    if known is not None:
        return known.value, ERROR_MESSAGES[known]
    if isinstance(exc.detail, str):
        return ErrorCode.http_error.value, exc.detail
    return ErrorCode.http_error.value, ERROR_MESSAGES[ErrorCode.http_error]

async def http_exception_handler(request: Request, exc: HTTPException):
    known = isinstance(exc, ApiError) or _known_code(exc.detail) is not None
    code, message = _http_error_fields(exc)
    detail = code if known else (exc.detail if isinstance(exc.detail, str) else code)
    response_headers = exc.headers if exc.headers else None
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": detail,
            "error": {
                "code": code,
                "message": message,
                "request_id": _request_id(request),
            },
        },
        headers=response_headers,
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "error": {
                "code": ErrorCode.validation_error.value,
                "message": ERROR_MESSAGES[ErrorCode.validation_error],
                "details": errors,
                "request_id": _request_id(request),
            },
        },
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled application error",
        extra={"request_id": _request_id(request), "path": request.url.path},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_body(
            code=ErrorCode.internal_server_error,
            message=ERROR_MESSAGES[ErrorCode.internal_server_error],
            request_id=_request_id(request),
        ),
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
