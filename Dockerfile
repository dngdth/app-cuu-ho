# Stage 1: Builder
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.10.2 /uv /uvx /bin/

# Compile bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
ENV UV_LINK_MODE=copy

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy source code
COPY ./app /app/app
COPY ./ai /app/ai
COPY ./main.py /app/main.py

# Sync the project
RUN uv sync --frozen

# -------------------------------------------
# Stage 2: Final slim image
FROM python:3.12-slim

# Install PostgreSQL client library (required by psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/

# Copy only what we need from the builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/ai /app/ai
COPY --from=builder /app/main.py /app/main.py

# Copy alembic for migrations
COPY ./alembic.ini /app/alembic.ini
COPY ./alembic /app/alembic

# Copy scripts (optional)
COPY ./scripts /app/scripts

EXPOSE 8091

# Use uvicorn to serve the app with multiple workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8091", "--workers", "1"]
