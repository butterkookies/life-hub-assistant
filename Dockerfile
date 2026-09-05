# ==========================================
# Stage 1: Build React/Vite PWA Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/web

# Install dependencies
COPY web/package*.json ./
RUN npm ci

# Build production static assets (web/dist)
COPY web/ ./
RUN npm run build

# ==========================================
# Stage 2: Python FastAPI Backend Runtime
# ==========================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY . .

# Copy compiled frontend from builder stage into web/dist
COPY --from=frontend-builder /app/web/dist ./web/dist

# Expose default port
EXPOSE 8000

# Start FastAPI server, dynamically binding to $PORT provided by Render/Railway/Fly
CMD ["sh", "-c", "python -m uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
