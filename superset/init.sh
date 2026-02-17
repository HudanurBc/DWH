#!/usr/bin/env bash
set -euo pipefail

echo "==> Superset: db upgrade"
superset db upgrade

echo "==> Superset: create admin (idempotent)"
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER}" \
  --firstname "${SUPERSET_ADMIN_FIRSTNAME}" \
  --lastname "${SUPERSET_ADMIN_LASTNAME}" \
  --email "${SUPERSET_ADMIN_EMAIL}" \
  --password "${SUPERSET_ADMIN_PASSWORD}" || true

echo "==> Superset: init"
superset init
# Import DB connection / datasources (idempotent)
#if [ -f /app/import/datasources.zip ]; then
# echo "==> Importing Superset datasources (DB connections)..."
 # superset import-datasources /app/import/datasources.zip || true
#fi


# OPTIONAL sanity output
echo "==> Superset users:"
superset fab list-users || true

echo "==> Start Superset (gunicorn)"
exec gunicorn \
  --bind "0.0.0.0:8088" \
  --workers 2 \
  --timeout 120 \
  "superset.app:create_app()"

