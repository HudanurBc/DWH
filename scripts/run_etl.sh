#!/usr/bin/env bash
set -euo pipefail

mkdir -p /app/logs
LOG_FILE="/app/logs/etl_$(date +%Y-%m).log"

echo "=== ETL START $(date -u) ===" | tee -a "$LOG_FILE"

python etl/extract/extract_aktin.py 2>&1 | tee -a "$LOG_FILE"
python etl/extract/extract_dwd_temp.py 2>&1 | tee -a "$LOG_FILE"
python etl/extract/extract_dwd_precip.py 2>&1 | tee -a "$LOG_FILE"
python etl/extract/extract_dwd_sun.py 2>&1 | tee -a "$LOG_FILE"

python etl/transform/transform_aktin_monthly.py 2>&1 | tee -a "$LOG_FILE"
python etl/transform/transform_weather_monthly_de.py 2>&1 | tee -a "$LOG_FILE"

python etl/load/load.py 2>&1 | tee -a "$LOG_FILE"

echo "=== ETL END $(date -u) ===" | tee -a "$LOG_FILE"
