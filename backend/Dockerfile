# Backend image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/app/data

WORKDIR /app

# System deps for pdf/docx parsing (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY data ./data

# Pre-download the embedding model so the first request is fast.
# (Layer-cached; skipped automatically if already present.)
RUN python -c "from langchain_community.embeddings import HuggingFaceEmbeddings; \
    HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')" \
    || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Seed on boot if the store is empty, then launch uvicorn.
CMD ["sh", "-c", "python -m app.seed_on_startup && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
