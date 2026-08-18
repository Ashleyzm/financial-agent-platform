"""Stable JSON error envelope and request tracing for the control-plane API."""

from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from packages.contracts import APIError, APIErrorEnvelope


class PlatformAPIError(RuntimeError):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        module_code: str = "PLT-03",
        task_id: UUID | None = None,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.module_code = module_code
        self.task_id = task_id
        self.retryable = retryable
        self.details = details or {}


def _request_trace_id(request: Request) -> UUID:
    return request.state.trace_id


def _response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    module_code: str,
    task_id: UUID | None = None,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = APIErrorEnvelope(
        error=APIError(
            code=code,
            message=message,
            module_code=module_code,
            trace_id=_request_trace_id(request),
            task_id=task_id,
            retryable=retryable,
            details=details or {},
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def install_error_handling(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_trace_id(request: Request, call_next):
        supplied = request.headers.get("X-Trace-ID")
        try:
            request.state.trace_id = UUID(supplied) if supplied else uuid4()
        except ValueError:
            request.state.trace_id = uuid4()
        response = await call_next(request)
        response.headers["X-Trace-ID"] = str(request.state.trace_id)
        return response

    @app.exception_handler(PlatformAPIError)
    async def handle_platform_error(request: Request, exc: PlatformAPIError) -> JSONResponse:
        return _response(
            request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            module_code=exc.module_code,
            task_id=exc.task_id,
            retryable=exc.retryable,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _response(
            request,
            status_code=422,
            code="request_validation_failed",
            message="请求参数校验失败",
            module_code="PLT-03",
            details={"errors": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _response(
            request,
            status_code=exc.status_code,
            code="http_error",
            message=str(exc.detail),
            module_code="PLT-01",
        )
