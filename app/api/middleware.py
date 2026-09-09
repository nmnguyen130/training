import uuid
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.context import RequestContext, bind_context
from app.core.security import decode_token


class RequestContextMiddleware:
    """ASGI middleware for request tracking, token extraction, and process timing."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))

        # 1. Tracing IDs
        req_id = headers.get(b"x-request-id", b"").decode("utf-8") or str(uuid.uuid4())
        trace_id = headers.get(b"x-trace-id", b"").decode("utf-8") or req_id

        # 2. Decode token if present (bind to context)
        user_id = None
        role = None
        auth_header = headers.get(b"authorization", b"").decode("utf-8")

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = decode_token(token, expected_type="access")
                user_id = uuid.UUID(payload["sub"]) if payload.get("sub") else None
                role = payload.get("role")
            except Exception:
                pass  # Invalid or expired token will be handled by auth dependencies

        ctx = RequestContext(
            request_id=req_id,
            trace_id=trace_id,
            user_id=user_id,
            role=role,
        )

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                headers_list.append((b"x-request-id", req_id.encode("utf-8")))
                headers_list.append((b"x-trace-id", trace_id.encode("utf-8")))
                message["headers"] = headers_list
            await send(message)

        with bind_context(ctx):
            await self.app(scope, receive, send_wrapper)
