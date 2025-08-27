# syntax=docker/dockerfile:1

# Multi-architecture support - optimized for ARM64/Apple Silicon
FROM ubuntu:22.04

LABEL version="1.0.0"
LABEL description="A large developer focused MCP server for running with AI more easily."
LABEL author='RA86-dev'

# Prevents Python from writing pyc files and keeps Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies with retry logic for hash sum mismatch issues
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update --fix-missing || apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        wget \
        gnupg \
        ca-certificates \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt

# Install Playwright and dependencies
RUN playwright install chromium firefox webkit
RUN playwright install-deps

# Copy the source code into the container
COPY . .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose the port that the application listens on
EXPOSE 8000

# Run the application
CMD ["python3", "main.py", "--transport", "sse", "--verbose"]
