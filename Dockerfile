# syntax=docker/dockerfile:1

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a non-root user to run the bot
RUN groupadd --system --gid 1001 voicecord \
    && useradd  --system --uid 1001 --gid voicecord --create-home --shell /bin/bash voicecord

WORKDIR /app

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=voicecord:voicecord . .

USER voicecord

# Lightweight health check: verify the process is still alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD pgrep -f "python main.py" >/dev/null || exit 1

CMD ["python", "-u", "main.py"]
