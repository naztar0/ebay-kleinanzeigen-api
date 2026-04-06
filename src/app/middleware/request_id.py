from __future__ import annotations

import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Aligns with common proxy limits; rejects abuse and log-forging payloads.
_MAX_X_REQUEST_ID_LEN = 128


def resolve_x_request_id(header_value: str | None) -> str:
    """Return a safe request ID for logging and response headers.

    If *header_value* is missing, empty after strip, too long, or contains
    non-printable ASCII, returns a new UUID4 string instead of trusting input.
    """
    if header_value is None:
        return str(uuid.uuid4())
    stripped = header_value.strip()
    if not stripped or len(stripped) > _MAX_X_REQUEST_ID_LEN:
        return str(uuid.uuid4())
    for ch in stripped:
        o = ord(ch)
        if o < 32 or o > 126:
            return str(uuid.uuid4())
    return stripped


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for log correlation.

    Reads X-Request-ID from incoming headers when present and safe, otherwise
    generates a UUID4. The value is echoed in the response header and bound to
    all log records for that request via Loguru contextvars.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        raw = request.headers.get("X-Request-ID")
        rid = resolve_x_request_id(raw)
        with logger.contextualize(request_id=rid):
            response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
