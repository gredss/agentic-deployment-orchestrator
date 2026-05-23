# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set metadata labels
LABEL maintainer="DevOps Team"
LABEL description="Python Flask Application for OpenShift"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
# Application version
ENV APP_VERSION=1.0.0
# Environment name
ENV ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create non-root user for security
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run application with gunicorn
# --bind: Bind to all interfaces on port 8080
# --workers: Number of worker processes (2 * CPU cores + 1)
# --timeout: Worker timeout in seconds
# --access-logfile: Access log location
# --error-logfile: Error log location
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app:app"]

# Made with Bob
