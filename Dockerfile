# syntax=docker/dockerfile:1
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using pip (system-wide)
RUN uv pip install --no-cache -r pyproject.toml

# Copy application code
COPY . .

# Run the application
CMD ["python", "main.py"]
