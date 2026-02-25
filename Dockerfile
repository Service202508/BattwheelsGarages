# ============================================================
# BATTWHEELS OS — Multi-stage Production Dockerfile
# Stage 1: Build React frontend (CRA + craco)
# Stage 2: Python backend serving API + static frontend
# ============================================================

# Stage 1: Frontend build
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/yarn.lock* ./
RUN yarn install --frozen-lockfile --network-timeout 120000
COPY frontend/ ./
ENV GENERATE_SOURCEMAP=false
ARG REACT_APP_BACKEND_URL=""
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
RUN yarn build

# Stage 2: Backend + serve built frontend
FROM python:3.11-slim
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY docs/ ./docs/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Environment defaults (overridden at runtime)
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Health check (used by Railway + docker-compose)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
