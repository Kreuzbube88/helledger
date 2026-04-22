# Stage 1: build frontend
FROM --platform=linux/amd64 node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/ .
RUN npm ci && npm run build

# Stage 2: Python application
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gosu \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --system --no-create-home --group helledger \
    && mkdir -p /data /backups \
    && chown helledger:helledger /data /backups

COPY backend/app/ ./app/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini .
COPY --from=frontend-builder /build/dist ./frontend/dist/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV HELLEDGER_FRONTEND=/app/frontend/dist

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s \
    CMD curl -f http://localhost:3000/api/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
