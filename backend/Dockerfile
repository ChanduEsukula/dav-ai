FROM python:3.13-slim@sha256:4873c73fa393882cf10f9d1054c928e95201c1559ca2107c1589786ece10f49f
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DAVAI_ENV=production
COPY backend/requirements-runtime.lock .
RUN python -m pip install --no-cache-dir --require-hashes -r requirements-runtime.lock
# Root .dockerignore admits only the read-only API source, excluding offline tools/data.
COPY backend/app ./app
RUN useradd --create-home davai
USER davai
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log --no-proxy-headers --workers 1 --limit-concurrency 32 --timeout-keep-alive 5"]
