from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportImplicitOverride=false

import time
import uuid
from collections.abc import Awaitable
from collections.abc import Callable

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ai_visibility.observability.logging_config import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        incoming_id = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming_id or f"req_{uuid.uuid4().hex[:12]}"
        token = request_id_var.set(request_id)

        start = time.perf_counter()
        method = request.method
        path = request.url.path
        query = request.url.query

        if not _is_noisy(path):
            logger.info(
                "request.start {} {}",
                method,
                _format_path(path, query),
                request_method=method,
                request_path=path,
                request_query=query,
                client_host=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent", ""),
            )

        status_code = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            logger.exception(
                "request.error {} {} — unhandled exception",
                method,
                _format_path(path, query),
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            if response is not None:
                response.headers[REQUEST_ID_HEADER] = request_id
            if not _is_noisy(path):
                log_at = logger.warning if status_code >= 500 else logger.info
                log_at(
                    "request.end {} {} -> {} ({}ms)",
                    method,
                    _format_path(path, query),
                    status_code,
                    duration_ms,
                    request_method=method,
                    request_path=path,
                    response_status=status_code,
                    duration_ms=duration_ms,
                )
            request_id_var.reset(token)


def _is_noisy(path: str) -> bool:
    return path in {"/api/v1/health", "/favicon.ico", "/favicon.svg"}


def _format_path(path: str, query: str) -> str:
    if not query:
        return path
    return f"{path}?{query}"
