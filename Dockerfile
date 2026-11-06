# syntax=docker/dockerfile:1

FROM node:24-bookworm-slim AS frontend-build
WORKDIR /build/frontend
RUN npm install --global pnpm@11.25.0
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
# Vite embeds this public path at build time. No model/API secrets belong here.
ENV VITE_API_BASE=/api/v1
RUN pnpm build

FROM python:3.11-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODE=demo \
    EDUMATE_DATA_DIR=/data
RUN apt-get update \
    && apt-get install --no-install-recommends --yes nginx ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 edumate \
    && useradd --uid 10001 --gid 10001 --create-home edumate \
    && mkdir -p /app/backend /data /usr/share/nginx/html \
    && chown -R edumate:edumate /app /data
WORKDIR /app/backend
COPY backend/requirements-lock.txt ./requirements-lock.txt
RUN python -m pip install --no-cache-dir -r requirements-lock.txt
COPY --chown=edumate:edumate backend/app/ ./app/
COPY --chown=edumate:edumate docker/ /app/docker/
COPY --from=frontend-build /build/frontend/dist/ /usr/share/nginx/html/
USER edumate
EXPOSE 8080
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=15s --timeout=5s --start-period=25s --retries=5 \
    CMD ["python", "/app/docker/healthcheck.py"]
CMD ["python", "/app/docker/start.py"]
