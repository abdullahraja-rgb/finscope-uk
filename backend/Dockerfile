FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV CONFIG_DIR=/app/config
ENV CORS_ORIGINS=http://localhost:3000

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/app /app/backend/app
COPY config /app/config
COPY data/sample /app/data/sample

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
