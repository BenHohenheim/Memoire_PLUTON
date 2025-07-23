# syntax=docker/dockerfile:1.4
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY main.py .
COPY pluton_model.pkl .
COPY pluton_label_encoder.pkl .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
