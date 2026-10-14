FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --no-dev --no-install-project

# Copy application code
COPY src/ src/
COPY alembic.ini ./
COPY start.sh ./

# Install the project itself
RUN uv sync --no-dev && chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
