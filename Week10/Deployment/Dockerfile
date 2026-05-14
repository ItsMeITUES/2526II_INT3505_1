FROM python:3.12-slim

# Security: run as non-root
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Install deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Non-root user
USER app

# Expose app + metrics (same port via /metrics)
EXPOSE 8000

# Production: 4 workers, stdout logging, 30s graceful timeout
CMD ["gunicorn", "wsgi:app", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--timeout", "30", \
     "--keep-alive", "5"]
