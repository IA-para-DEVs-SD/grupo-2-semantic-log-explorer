# ---- Stage: base ----
# Runtime dependencies only
FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml backend/uv.lock ./backend/

RUN cd backend && uv sync --frozen

# ---- Stage: test ----
# Adds test dependencies (pytest, hypothesis, etc.)
FROM base AS test

RUN cd backend && uv sync --frozen --group test

# ---- Stage: production ----
# Minimal image with source code and runtime deps only
FROM base AS production

COPY backend/ ./backend/

EXPOSE 8000

CMD ["backend/.venv/bin/uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
