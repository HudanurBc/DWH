FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl tzdata postgresql-client \
  && rm -rf /var/lib/apt/lists/*

ENV TZ=Europe/Berlin

# supercronic (Cron runner for containers)
RUN curl -fsSL -o /usr/local/bin/supercronic \
    https://github.com/aptible/supercronic/releases/download/v0.2.32/supercronic-linux-amd64 \
  && chmod +x /usr/local/bin/supercronic

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod +x /app/scripts/run_etl.sh /app/etl/entrypoint.sh

ENTRYPOINT ["/app/etl/entrypoint.sh"]
