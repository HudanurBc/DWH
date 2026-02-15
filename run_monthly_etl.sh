#!/bin/bash
set -e  # bei Fehler abbrechen

# ===== Pfade anpassen =====
PROJECT_ROOT="/Users/hudanurbilgic/Projects/DWH"
VENV_PATH="$PROJECT_ROOT/.venv"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/etl_$(date +%Y-%m).log"

echo "=== ETL START $(date) ===" >> "$LOG_FILE"

# ===== venv aktivieren =====
if [ -f "$VENV_PATH/bin/activate" ]; then
  source "$VENV_PATH/bin/activate"
else
  echo "WARN: No venv at $VENV_PATH/bin/activate - using system python" >> "$LOG_FILE"
fi

cd "$PROJECT_ROOT"

# ===== Extract =====
python etl/extract/extract_aktin.py >> "$LOG_FILE" 2>&1
python etl/extract/extract_dwd_temp.py >> "$LOG_FILE" 2>&1
python etl/extract/extract_dwd_precip.py >> "$LOG_FILE" 2>&1
python etl/extract/extract_dwd_sun.py >> "$LOG_FILE" 2>&1

# ===== Transform =====
python etl/transform/transform_aktin_monthly.py >> "$LOG_FILE" 2>&1
python etl/transform/transform_weather_monthly_de.py >> "$LOG_FILE" 2>&1

# ===== Load =====
python etl/load/load.py >> "$LOG_FILE" 2>&1

echo "=== ETL END $(date) ===" >> "$LOG_FILE"

