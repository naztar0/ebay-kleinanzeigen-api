from __future__ import annotations

import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for log correlation.

    Reads X-Request-ID from incoming headers when present, otherwise generates
    a UUID4. The value is echoed back in the response header and bound to all
    log records emitted during that request via Loguru contextvars.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        with logger.contextualize(request_id=rid):
            response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
