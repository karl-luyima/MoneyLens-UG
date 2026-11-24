
# ---------------------------------------------------------
# Stage 1: Build backend dependencies
# ---------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir .

# ---------------------------------------------------------
# Stage 2: API runtime
# ---------------------------------------------------------
FROM python:3.12-slim AS api

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup appuser

COPY --from=builder /usr/local /usr/local

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------------------------------------------------------
# Stage 3: Streamlit frontend
# ---------------------------------------------------------
FROM api AS frontend

USER root

COPY frontend/requirements.txt ./frontend/requirements.txt

RUN pip install --no-cache-dir -r frontend/requirements.txt

COPY frontend ./frontend

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
