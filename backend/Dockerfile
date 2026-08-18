FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir .

RUN useradd --create-home --shell /bin/bash appuser

# The RAG index is written at runtime, but /app is root-owned and the process
# runs as `appuser` — without this the first indexing attempt dies on EACCES.
# Mount a volume here in any deployment that should survive a redeploy.
RUN mkdir -p /app/data/rag && chown -R appuser:appuser /app/data
ENV RAG_INDEX_DIR=/app/data/rag
VOLUME ["/app/data"]

USER appuser

EXPOSE 8000
ENV PORT=8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",\"8000\")}/api/v1/health')" || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
