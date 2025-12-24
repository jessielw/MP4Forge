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

# Stage 2: Python runtime with backend - based on GPAC's official image
FROM gpac/ubuntu:latest

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3.12-venv \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.12 /usr/bin/python

# Verify mp4box is available (should be pre-installed in gpac/ubuntu image)
RUN MP4Box -version

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv

# Add venv to PATH so we use it by default
ENV PATH="/opt/venv/bin:$PATH"

# Copy Python project files
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Copy source code
COPY backend/ ./backend/
COPY core/ ./core/

# Install Python dependencies into venv
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
