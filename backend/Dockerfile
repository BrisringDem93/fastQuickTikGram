# ── Stage 1: build dependencies ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# System deps for building psycopg2, cryptography, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ── Stage 2: shared runtime base ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

# Runtime system deps shared by API + workers
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home appuser

# ── Stage 3: app filesystem shared by API + workers ─────────────────────────
FROM runtime-base AS app-base

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Set ownership
RUN chown -R appuser:appgroup /app

# ── Stage 4: API / beat runtime (lean, no ffmpeg) ───────────────────────────
FROM app-base AS api-runtime

USER appuser

EXPOSE 8000

# Default: run the FastAPI application with Uvicorn.
# --timeout-keep-alive 600: keep TCP connections alive for up to 10 minutes
# so that large video uploads (up to 500 MB) are not severed mid-transfer.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--timeout-keep-alive", "600"]


# ── Stage 5: worker runtime (includes ffmpeg) ───────────────────────────────
FROM app-base AS worker-runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

USER appuser

CMD ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
