"""
Middleware which adds a correlation id to the response headers and logs.
https://github.com/snok/asgi-correlation-id/blob/main/README.md#integration-with-uvicorn
"""

import logging

from asgi_correlation_id import CorrelationIdFilter
from pydantic.v1.utils import deep_update
from uvicorn.config import LOGGING_CONFIG

logging_format_prefix = "%(asctime)s [%(name)-14s]"


def get_uvicorn_log_config() -> dict:
    """
    Return a logging config for uvicorn with timestamps added,
    and the correlation-id added to access logs.
    """
    return deep_update(
        LOGGING_CONFIG,
        {
            "handlers": {"access": {"filters": [CorrelationIdFilter()]}},
            "formatters": {
                "access": {
                    "fmt": logging_format_prefix
                    + " %(levelprefix)s [%(correlation_id)s] %(message)s",
                },
                # Configuring the default formatter impacts the appliction lifecycle logs.
                "default": {
                    "fmt": f"{logging_format_prefix} %(levelprefix)s %(message)s",
                },
            },
        },
    )


def configure_logging():
    # This setup impacts the logs sent from our own code as well as logs from httpx.
    console_handler = logging.StreamHandler()
    console_handler.addFilter(CorrelationIdFilter())
    logging.basicConfig(
        handlers=[console_handler],
        format=logging_format_prefix
        + " %(levelname)-9s [%(correlation_id)s] %(message)s",
        level=logging.INFO,
    )
