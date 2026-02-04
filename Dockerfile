FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd -m appuser

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY gee_flood /app/gee_flood
COPY config /app/config
COPY scripts /app/scripts

USER appuser

EXPOSE 8000
CMD ["uvicorn", "gee_flood.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
