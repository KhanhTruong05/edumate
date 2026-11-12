# Build context: repository root
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 edumate \
    && useradd --uid 10001 --gid 10001 --create-home edumate
WORKDIR /app/ai
COPY ai/ ./
RUN python -m pip install --no-cache-dir '.[service]'
USER edumate
EXPOSE 8001
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8001/health', timeout=4).close()"]
CMD ["python", "-m", "uvicorn", "edumate_ai.service:create_app", "--factory", "--host", "0.0.0.0", "--port", "8001", "--no-proxy-headers"]
