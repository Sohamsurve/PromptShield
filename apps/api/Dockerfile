FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl tesseract-ocr && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml /app/apps/api/pyproject.toml
COPY apps/api/src /app/apps/api/src
COPY fixtures /app/fixtures
COPY eval /app/eval

RUN pip install --no-cache-dir /app/apps/api

ENV PYTHONPATH=/app/apps/api/src
EXPOSE 8000
CMD ["uvicorn", "promptshield.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
