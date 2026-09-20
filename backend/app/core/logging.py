"""Centralized logging configuration.

Configures the root logger and uvicorn loggers so application logs and
server logs share a single, consistent format.
"""
import logging
import logging.config
import sys
from typing import Any, Dict

from app.core.config import settings


def _build_config() -> Dict[str, Any]:
    fmt = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if not settings.LOG_JSON
        else '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
    )

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": fmt, "datefmt": "%Y-%m-%d %H:%M:%S"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
                "level": settings.LOG_LEVEL,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": settings.LOG_LEVEL, "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": settings.LOG_LEVEL, "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": settings.LOG_LEVEL, "propagate": False},
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }


def configure_logging() -> None:
    logging.config.dictConfig(_build_config())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
