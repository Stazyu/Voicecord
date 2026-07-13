# syntax=docker/dockerfile:1

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a non-root user to run the bot, and install curl for the healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 voicecord \
    && useradd  --system --uid 1001 --gid voicecord --create-home --shell /bin/bash voicecord

WORKDIR /app

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=voicecord:voicecord . .

USER voicecord

# Health endpoint exposed by main.py (configurable via HEALTH_PORT, default 8080)
EXPOSE 8080

# Probe the in-process HTTP health server. The server returns 200 only if the
# Discord gateway heartbeat is fresh, otherwise 503, which Docker treats as
# unhealthy and triggers a restart of the container.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${HEALTH_PORT:-8080}/health" >/dev/null || exit 1

CMD ["python", "-u", "main.py"]
