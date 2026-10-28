# Build the browser app separately; Node is not needed in the running service.
FROM node:24-bookworm-slim AS frontend
WORKDIR /build/frontend
RUN npm install --global corepack --force
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN corepack pnpm install --frozen-lockfile
COPY frontend/ ./
# A restricted browser key is public by design. Never pass server secrets here.
ARG VITE_GOOGLE_MAPS_API_KEY
ENV VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY
RUN corepack pnpm build

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    CIVICFLUX_ROOT=/app CIVICFLUX_DB=/app/var/civicflux.sqlite3 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements-serving.txt requirements-backend.txt ./
RUN python -m pip install -r requirements-serving.txt
COPY . .
COPY --from=frontend /build/frontend/dist ./frontend/dist
RUN useradd --uid 10001 --create-home civicflux && mkdir -p /app/var \
    && chown -R civicflux:civicflux /app/var
USER civicflux
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8001')+'/api/health', timeout=4)"
CMD ["sh", "-c", "exec python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
