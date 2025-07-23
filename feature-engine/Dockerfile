FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY feature_engine.py .
RUN chmod +x feature_engine.py

CMD ["./feature_engine.py"]
