# Build context: repository root (backend uses the shared AI schema/citation package)
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODE=demo \
    EDUMATE_DATA_DIR=/data
RUN groupadd --gid 10001 edumate \
    && useradd --uid 10001 --gid 10001 --create-home edumate \
    && mkdir -p /app/backend /data \
    && chown -R edumate:edumate /app /data
WORKDIR /app/backend
COPY backend/requirements-lock.txt ./requirements-lock.txt
RUN python -m pip install --no-cache-dir -r requirements-lock.txt
COPY ai/ /app/ai/
RUN python -m pip install --no-cache-dir --no-deps /app/ai
COPY --chown=edumate:edumate backend/app/ ./app/
USER edumate
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=4).close()"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers"]
