"""Request logging: one line when a request arrives (with its path) and one when it completes.

Logged per request: request id, method, path, query string (secrets redacted), client address, status code,
latency and response size. The message text is never logged, because users may type personal or farm details.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request
from starlette.responses import Response

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s | %(levelname)-5s | %(name)s | rid=%(request_id)s | %(message)s"
SKIP_PATHS = frozenset({"/docs", "/redoc", "/openapi.json", "/favicon.ico"})
_SECRET_PARAM = re.compile(r"(?i)((?:token|key|password|secret)=)[^&]*")

logger = logging.getLogger("chatbot.requests")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def configure_logging(level: int = logging.INFO, log_file: Path | None = Path("logs/requests.log")) -> None:
    """Console plus a rotating file. Call once at start-up, before the app is created."""
    formatter = logging.Formatter(LOG_FORMAT)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5, encoding="utf-8"))
    root = logging.getLogger()
    root.handlers.clear()
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.addFilter(_RequestIdFilter())
        root.addHandler(handler)
    root.setLevel(level)
    # Uvicorn's own access line duplicates ours and lacks the request id; run.py passes --no-access-log.
    logging.getLogger("uvicorn.access").disabled = True


def _redact(query: str) -> str:
    return _SECRET_PARAM.sub(r"\1***", query)


def install_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        token = request_id_ctx.set(rid)
        path = request.url.path
        query = _redact(request.url.query)
        target = f"{path}?{query}" if query else path
        client = request.client.host if request.client else "-"
        visible = path not in SKIP_PATHS

        if visible:
            logger.info("received %s %s from %s", request.method, target, client)
        started = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            logger.exception("failed %s %s after %.1f ms", request.method, target,
                             (time.perf_counter() - started) * 1000)
            request_id_ctx.reset(token)
            raise

        route = request.scope.get("route")
        template = getattr(route, "path", path)  # the route template, e.g. /chat/
        size = response.headers.get("content-length", "-")
        if visible:
            logger.info(
                "completed %s %s -> %s in %.1f ms (route=%s, bytes=%s)",
                request.method, target, response.status_code,
                (time.perf_counter() - started) * 1000, template, size,
            )
        response.headers["X-Request-ID"] = rid
        request_id_ctx.reset(token)
        return response
