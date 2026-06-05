# syntax=docker/dockerfile:1

# --- Stage 1: build the React frontend ---
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: backend + serve the built SPA ---
FROM python:3.12-slim
WORKDIR /app/backend

# Install Python deps (and the `app` package) from the backend project.
COPY backend/ ./
RUN pip install --no-cache-dir .

# Bring in the compiled frontend and tell FastAPI where it lives.
COPY --from=frontend /build/dist /app/frontend/dist
ENV FRONTEND_DIST=/app/frontend/dist

# Synthetic data the loaders read at runtime (data_loader resolves data/ as a
# sibling of backend/ via __file__, i.e. /app/data).
COPY data/ /app/data/

# Prefer the source tree over the site-packages copy so __file__-relative paths
# (data_loader's DATA_DIR) resolve against /app/backend, not site-packages.
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1

# Drop root: run the app as an unprivileged user.
RUN adduser --system --no-create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Railway injects $PORT; fall back to 8000 for local `docker run`.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
