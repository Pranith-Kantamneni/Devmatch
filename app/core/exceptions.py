import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("devmatch")


class AppException(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource already exists"


class InvalidCredentialsException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid credentials"


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Not allowed"


class ValidationException(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = "Validation error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = exc.errors()
        # Pydantic error ctx values may hold non-serializable objects
        # (e.g. ValueError) — coerce them to strings for a stable contract.
        safe_errors = []
        for error in errors:
            safe_error = dict(error)
            ctx = safe_error.get("ctx")
            if isinstance(ctx, dict):
                safe_error["ctx"] = {k: str(v) for k, v in ctx.items()}
            safe_errors.append(safe_error)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": safe_errors},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning("Integrity error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Resource already exists or conflicts with existing data"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
