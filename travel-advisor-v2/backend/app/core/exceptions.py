from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.config import settings


class AppError(Exception):
    """Base application error with code and message."""

    def __init__(self, code: int, message: str, detail: str = ""):
        self.code = code
        self.message = message
        self.detail = detail


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str = ""):
        super().__init__(
            code=404,
            message=f"{resource} not found",
            detail=identifier,
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(code=401, message=message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(code=403, message=message)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(code=422, message=message)


class RateLimitError(AppError):
    def __init__(self):
        super().__init__(code=429, message="Too many requests")


class LLMTimeoutError(AppError):
    def __init__(self):
        super().__init__(code=504, message="LLM request timed out")


class SearchUnavailableError(AppError):
    def __init__(self):
        super().__init__(code=503, message="Search service unavailable")


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "detail": exc.detail,
            }
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "detail": "",
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": str(exc),
                    "detail": type(exc).__name__,
                }
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "detail": "",
            }
        },
    )
