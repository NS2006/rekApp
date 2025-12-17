FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/uploads /tmp/processed

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--timeout", "400", "--workers", "2", "--threads", "8", "app:app"]