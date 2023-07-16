"""
Middleware which adds a correlation id to the response headers and logs.
See https://github.com/tiangolo/fastapi/discussions/8190
"""
import copy
import logging
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request, Response
from pydantic.utils import deep_update
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from uvicorn.config import LOGGING_CONFIG
from uvicorn.logging import AccessFormatter

_correlation_id_ctx_var: ContextVar[str] = ContextVar("correlation_id", default=None)

logging_format_prefix = "%(asctime)s [%(name)-14s]"


class UvicornAccessFormatter(AccessFormatter):
    """
    Add the correlation-id to uvicorn access logs
    """

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy.copy(record)
        recordcopy.__dict__.update({"correlation_id": _correlation_id_ctx_var.get()})
        return super().formatMessage(record=recordcopy)

    @classmethod
    @property
    def name(cls):
        return f"{cls.__module__}.{cls.__name__}"


def get_uvicorn_log_config() -> dict:
    """
    Return a logging config for uvicorn with timestamps added,
    and the correlation-id added to access logs.
    """
    return deep_update(
        LOGGING_CONFIG,
        {
            "formatters": {
                "access": {
                    "fmt": logging_format_prefix
                    + " %(levelprefix)s [%(correlation_id)s] %(message)s",
                    "()": UvicornAccessFormatter.name,
                },
                "default": {
                    "fmt": f"{logging_format_prefix} %(levelprefix)s %(message)s",
                },
            }
        },
    )


def update_httpx_logger():
    """
    Make the httpx module use our log handler.
    """
    custom_logger = logging.getLogger()
    httpx_logger = logging.getLogger("httpx")

    # Remove any existing handlers from the httpx logger
    for handler in httpx_logger.handlers[:]:
        httpx_logger.removeHandler(handler)

    # Add our custom logger as a handler
    httpx_logger.addHandler(custom_logger)


class LoggerMiddleware(BaseHTTPMiddleware):
    """
    Add an X-correlation-id header to responses.
    Add the correlation id to application logs.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        logging.getLogger().addFilter(self.add_correlation_id_to_log_record)

        logging.basicConfig(
            format=logging_format_prefix
            + " %(levelname)-9s [%(correlation_id)s] %(message)s",
            level=logging.INFO,
        )

    def add_correlation_id_to_log_record(self, record):
        record.correlation_id = _correlation_id_ctx_var.get()
        return True

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        correlation_id = str(uuid4())
        _correlation_id_ctx_var.set(correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        return response
