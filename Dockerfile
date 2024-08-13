FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv venv && \
    venv/bin/pip install --no-cache-dir -r requirements.txt

FROM builder as runner

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["venv/bin/streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
