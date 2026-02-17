#!/usr/bin/env bash
set -euo pipefail

echo "==> Ensuring DB schema exists..."
# WICHTIG: PGPASSWORD wird aus env gelesen (Compose setzt es)
export PGPASSWORD="${PGPASSWORD:-${PGPASSWORD:-}}"

# Warte kurz, falls DB zwar "healthy" ist, aber DNS/Netz gerade erst bereit ist
for i in {1..30}; do
  if psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT 1" >/dev/null 2>&1; then
    break
  fi
  echo "Waiting for DB... ($i/30)"
  sleep 2
done

# Schema anwenden (idempotent durch CREATE TABLE IF NOT EXISTS)
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -f /app/db/init/01_schema.sql

echo "==> Initial ETL run on container start..."
/app/scripts/run_etl.sh

echo "==> Starting supercronic scheduler..."
exec /usr/local/bin/supercronic /app/etl/cron/etl.cron
