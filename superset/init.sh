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

echo "==> Import datasources (optional)"
if [ -f /app/assets/datasources/datasources.zip ]; then
  echo "    Found /app/assets/datasources/datasources.zip"
  # Superset CLI command names differ slightly across versions/builds.
  # Try underscore version first, then dash version.
  superset import_datasources -p /app/assets/datasources/datasources.zip -u "${SUPERSET_ADMIN_USER}" || \
  superset import-datasources -p /app/assets/datasources/datasources.zip -u "${SUPERSET_ADMIN_USER}" || true
else
  echo "    No datasources.zip found, skipping."
fi

echo "==> Import dashboards (optional)"
if [ -f /app/assets/dashboards/my_dashboard.zip ]; then
  echo "    Found /app/assets/dashboards/my_dashboard.zip"
  # Same story: command/flags differ by version.
  # Try a couple of common variants.
  superset import_dashboards --path /app/assets/dashboards/my_dashboard.zip --username "${SUPERSET_ADMIN_USER}" || \
  superset import-dashboards -p /app/assets/dashboards/my_dashboard.zip -u "${SUPERSET_ADMIN_USER}" || true
else
  echo "    No dashboard zip found, skipping."
fi

# OPTIONAL sanity output
echo "==> Superset users:"
superset fab list-users || true

echo "==> Start Superset (gunicorn)"
exec gunicorn \
  --bind "0.0.0.0:8088" \
  --workers 2 \
  --timeout 120 \
  "superset.app:create_app()"
