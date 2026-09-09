import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str
    trace_id: str
    user_id: uuid.UUID | None = None
    role: str | None = None


_context: ContextVar[RequestContext | None] = ContextVar(
    "request_context", default=None
)


def current_context() -> RequestContext:
    ctx = _context.get()
    if ctx is None:
        raise RuntimeError("RequestContext accessed outside of request lifespan.")
    return ctx


def try_current_context() -> RequestContext | None:
    return _context.get()


@contextmanager
def bind_context(ctx: RequestContext):
    token = _context.set(ctx)
    try:
        yield ctx
    finally:
        _context.reset(token)
