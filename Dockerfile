# Multi-stage Dockerfile for MP4Forge Web Application
# Architecture: linux/amd64 (x64) only

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend_web/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend_web/ ./

# Build the frontend
RUN npm run build

# Stage 2: Python runtime with backend
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and install GPAC (mp4box) from official build server
# Always uses the latest build
RUN wget -q https://download.tsi.telecom-paristech.fr/gpac/new_builds/gpac_latest_head_linux64.deb && \
    apt-get update && \
    apt-get install -y ./gpac_latest_head_linux64.deb && \
    rm gpac_latest_head_linux64.deb && \
    rm -rf /var/lib/apt/lists/*

# Verify mp4box is available
RUN MP4Box -version

# Set working directory
WORKDIR /app

# Copy Python project files
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Copy source code
COPY backend/ ./backend/
COPY core/ ./core/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[core]" && \
    pip install --no-cache-dir fastapi uvicorn[standard] python-multipart websockets

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/build ./frontend_web/build

# Create necessary directories
RUN mkdir -p /app/runtime/logs /app/runtime/config /app/runtime/images

# Expose port for FastAPI
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MP4BOX_PATH=/usr/bin/MP4Box

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
