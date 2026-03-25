# Multi-stage Dockerfile for PIM Application
# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend (will use VITE_API_URL from build args or default to /api/v1)
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: Setup Backend
FROM python:3.11-slim AS backend-setup

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Final Runtime Image
FROM python:3.11-slim

WORKDIR /app

# Install nginx, supervisor and curl (for healthcheck)
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from backend-setup stage
COPY --from=backend-setup /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-setup /usr/local/bin /usr/local/bin

# Copy backend application (copy app module and other necessary files)
COPY backend/app /app/app
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/alembic.ini

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories
RUN mkdir -p /var/log/supervisor

# Expose port
EXPOSE 5006

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./pim.db
ENV PORT=5006

# Start supervisor (will manage both nginx and uvicorn)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
