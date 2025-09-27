# Multi-stage Dockerfile for SBIS API FastAPI application
# Stage 1: Builder
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Create necessary directories
RUN mkdir -p /app/logs /app/backups && \
    chown -R appuser:appuser /app

# Copy application code
COPY . .

# Change ownership of application files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "h11"]