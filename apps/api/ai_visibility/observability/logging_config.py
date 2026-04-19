from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from typing import Any

from loguru import logger

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[str] = ContextVar("user_id", default="-")


def get_request_id() -> str:
    return request_id_var.get()


def get_user_id() -> str:
    return user_id_var.get()


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _patch_context(record: dict[str, Any]) -> None:
    record["extra"].setdefault("request_id", request_id_var.get())
    record["extra"].setdefault("user_id", user_id_var.get())
    record["extra"].setdefault("service", "citetrack-api")


def configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    use_json = os.getenv("LOG_JSON", "").lower() in {"1", "true", "yes"}

    logger.remove()
    logger.configure(patcher=_patch_context)

    if use_json:
        logger.add(
            sys.stdout,
            level=log_level,
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
    else:
        fmt = (
            "<dim>{time:HH:mm:ss.SSS}</dim> "
            "<level>{level: <5}</level> "
            "<dim>rid={extra[request_id]} uid={extra[user_id]}</dim> "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            level=log_level,
            format=fmt,
            backtrace=True,
            diagnose=False,
            colorize=True,
        )

    root = logging.getLogger()
    root.handlers = [_InterceptHandler()]
    root.setLevel(log_level)
    for name in (
        "uvicorn",
        "uvicorn.error",
        "fastapi",
        "httpx",
        "prisma",
    ):
        target = logging.getLogger(name)
        target.handlers = []
        target.propagate = True

    access_log = logging.getLogger("uvicorn.access")
    access_log.handlers = []
    access_log.propagate = False
    access_log.disabled = True
