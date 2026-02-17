#!/usr/bin/env bash
set -euo pipefail

pick_flag() {
  # usage: pick_flag "<help_text>" "<longflag>" "<shortflag>"
  local help_txt="$1"
  local longflag="$2"
  local shortflag="$3"
  if echo "$help_txt" | grep -q -- "$longflag"; then
    echo "$longflag"
  else
    echo "$shortflag"
  fi
}

run_import() {
  # usage: run_import "<command>" "<file_or_dir>" "<username>"
  local cmd="$1"
  local path="$2"
  local user="$3"

  local help_txt
  if ! help_txt="$($cmd --help 2>&1)"; then
    echo "!!! ERROR: '$cmd --help' failed. Command not available?"
    return 1
  fi

  local user_flag path_flag
  user_flag="$(pick_flag "$help_txt" "--username" "-u")"
  path_flag="$(pick_flag "$help_txt" "--path" "-p")"

  echo "    -> using flags: ${path_flag} ${user_flag}"
  $cmd ${path_flag} "$path" ${user_flag} "$user"
}

echo "==> Superset: version"
superset version || true

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

echo "==> DEBUG: assets present?"
ls -lah /app/assets || true
ls -lah /app/assets/dashboards || true
ls -lah /app/assets/datasources || true

# ---- 1) DB Connection via YAML (stabiler als datasources.zip) ----
echo "==> Import DB connection from /app/assets/database.yaml (preferred)"
if [ -f /app/assets/database.yaml ]; then
  if ! run_import "superset import-datasources" "/app/assets/database.yaml" "${SUPERSET_ADMIN_USER}"; then
    # fallback underscore (falls dein Build das so nennt)
    run_import "superset import_datasources" "/app/assets/database.yaml" "${SUPERSET_ADMIN_USER}"
  fi
else
  echo "    No /app/assets/database.yaml found, skipping."
fi

# ---- 3) Dashboard import ----
echo "==> Import dashboard zip"
if [ -f /app/assets/dashboards/my_dashboard.zip ]; then
  if ! run_import "superset import-dashboards" "/app/assets/dashboards/my_dashboard.zip" "${SUPERSET_ADMIN_USER}"; then
    run_import "superset import_dashboards" "/app/assets/dashboards/my_dashboard.zip" "${SUPERSET_ADMIN_USER}"
  fi
else
  echo "    No /app/assets/dashboards/my_dashboard.zip found, skipping."
fi

echo "==> Superset users:"
superset fab list-users || true

echo "==> Start Superset (gunicorn)"
exec gunicorn \
  --bind "0.0.0.0:8088" \
  --workers 2 \
  --timeout 120 \
  "superset.app:create_app()"
