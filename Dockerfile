# Multi-stage build for Cloud Run Playwright PDF service
# Based on patterns from container_telethon_bot and china_navwarn

# Stage 1: Base Image with uv
FROM python:3.12-slim-bookworm AS base

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/var/cache/uv \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Install uv
RUN pip install uv

# Stage 2: Build Dependencies
FROM base AS builder

WORKDIR /app

# Install system dependencies for Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libxshmfence1 \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and install
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/var/cache/uv \
    uv pip install . --system --no-cache

# Install Chromium browser
RUN playwright install chromium && \
    rm -rf /root/.cache/ms-playwright/*.zip && \
    rm -rf /tmp/*

# Stage 3: Final Application Image
FROM base AS final

WORKDIR /app

# Create non-root user for security
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

# Install Chromium system dependencies (required at runtime)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libxshmfence1 \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy Playwright browsers from builder
COPY --from=builder /ms-playwright /ms-playwright

# Copy application code
COPY --chown=appuser:appuser app/ ./

# Switch to non-root user
USER appuser

# Set default PORT (Cloud Run uses 8080)
ENV PORT=8080

# Run uvicorn with exec form for signal handling
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port $PORT"]
