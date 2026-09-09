ARG PYTHON_VERSION=3.13
ARG UV_VERSION=0.12.5

# ==========================================
# Base UV binary image
# ==========================================
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:${PYTHON_VERSION}-slim-trixie AS builder

ARG UV_VERSION
COPY --from=uv /uv /uvx /bin/

WORKDIR /app

# Enable bytecode pre-compilation for faster runtime cold start
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_INSTALLER_METADATA=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install production dependencies only using BuildKit cache & bind mounts
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock,readonly \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml,readonly \
    uv sync --frozen --no-install-project --no-dev

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:${PYTHON_VERSION}-slim-trixie AS runtime

WORKDIR /app

# Security: Non-root dedicated application user (UID 10001)
RUN groupadd --system --gid 10001 app && \
    useradd --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

# Copy pre-built virtualenv with production dependencies
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy project source files & migrations
COPY --chown=app:app app ./app
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./alembic.ini

USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
