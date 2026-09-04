"""Request correlation identifier middleware and context tracking."""

import re
import uuid
from contextvars import ContextVar
from typing import Optional
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"

# Context variable tracking the request ID for the current async task
_request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

_SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")


def get_request_id() -> Optional[str]:
    """Retrieve the current request correlation ID from context."""
    return _request_id_ctx_var.get()


def _sanitize_incoming_id(raw_id: str) -> Optional[str]:
    """Validate and sanitize client-provided request ID."""
    raw_id = raw_id.strip()
    if _SAFE_ID_REGEX.match(raw_id):
        return raw_id
    return None


class RequestIDMiddleware:
    """Pure ASGI middleware managing request correlation IDs on requests and responses."""

    def __init__(self, app: ASGIApp, header_name: str = REQUEST_ID_HEADER) -> None:
        self.app = app
        self.header_name = header_name
        self.header_name_bytes = header_name.lower().encode("latin-1")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract existing request / correlation ID from incoming headers
        request_id: Optional[str] = None
        headers = scope.get("headers", [])
        for name, value in headers:
            name_lower = name.lower()
            if name_lower in (b"x-request-id", b"x-correlation-id"):
                try:
                    candidate = value.decode("latin-1")
                    request_id = _sanitize_incoming_id(candidate)
                    if request_id:
                        break
                except Exception:
                    pass

        # Generate a new request ID if none was supplied or valid
        if not request_id:
            request_id = f"req-{uuid.uuid4().hex}"

        # Populate request state and context variable
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id
        token = _request_id_ctx_var.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                # Ensure header is present on outgoing HTTP response
                response_headers = list(message.get("headers", []))
                # Remove any existing instance of the header to prevent duplication
                response_headers = [
                    (k, v) for k, v in response_headers if k.lower() != self.header_name_bytes
                ]
                response_headers.append((self.header_name_bytes, request_id.encode("latin-1")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            _request_id_ctx_var.reset(token)
