FROM python:3.13-slim

# Install HiGHS solver binary
RUN apt-get update && \
    apt-get install -y --no-install-recommends highs curl && \
    rm -rf /var/lib/apt/lists/*

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Create app user and directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/_temp && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser backend ./backend
COPY --chown=appuser:appuser backend/alembic ./alembic
COPY --chown=appuser:appuser backend/alembic.ini ./alembic.ini

# Switch to non-root user
USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
