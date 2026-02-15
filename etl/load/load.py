import os
from pathlib import Path
from datetime import date

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


# =========================
# Paths / Inputs
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../DWH

AKTIN_CSV = PROJECT_ROOT / "data/processed/aktin_monthly.csv"
WEATHER_CSV = PROJECT_ROOT / "data/processed/weather_monthly_de.csv"


# =========================
# Helpers
# =========================
def season_from_month(m: int) -> str:
    if m in (12, 1, 2):
        return "Winter"
    if m in (3, 4, 5):
        return "Frühling"
    if m in (6, 7, 8):
        return "Sommer"
    return "Herbst"


def connect():
    """
    Uses env vars (best for Docker/Airflow):
      PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
    Falls back to your local docker-compose defaults.
    """
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "mydb"),
        user=os.getenv("PGUSER", "admin"),
        password=os.getenv("PGPASSWORD", "passwort"),
    )


def ensure_constraints(cur):
    """
    PostgreSQL supports CREATE INDEX IF NOT EXISTS,
    but NOT: ALTER TABLE ... ADD CONSTRAINT IF NOT EXISTS
    -> Use DO blocks for idempotent constraint creation.
    """
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dim_syndrom_bez') THEN
            ALTER TABLE dim_syndrom
            ADD CONSTRAINT uq_dim_syndrom_bez UNIQUE (bezeichnung);
        END IF;
    END$$;
    """)

    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dim_edtype_typ') THEN
            ALTER TABLE dim_edtype
            ADD CONSTRAINT uq_dim_edtype_typ UNIQUE (typ);
        END IF;
    END$$;
    """)

    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dim_altersgruppe') THEN
            ALTER TABLE dim_altersgruppe
            ADD CONSTRAINT uq_dim_altersgruppe UNIQUE (altersgruppe);
        END IF;
    END$$;
    """)

    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dim_datum_datum') THEN
            ALTER TABLE dim_datum
            ADD CONSTRAINT uq_dim_datum_datum UNIQUE (datum);
        END IF;
    END$$;
    """)

    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_fact_grain') THEN
            ALTER TABLE fakt_erkrankungen
            ADD CONSTRAINT uq_fact_grain UNIQUE (datum_key, syndrom_key, altersgruppe_key, edtype_key);
        END IF;
    END$$;
    """)


def upsert_dim_text(cur, table: str, col: str, values: list[str]):
    """Insert unique string values into a dimension table."""
    cleaned = []
    for v in values:
        if pd.isna(v):
            continue
        s = str(v).strip()
        if s == "" or s.lower() == "nan":
            continue
        cleaned.append(s)

    unique_vals = sorted(set(cleaned))
    if not unique_vals:
        return 0

    sql = f"""
        INSERT INTO {table} ({col})
        VALUES %s
        ON CONFLICT ({col}) DO NOTHING;
    """
    execute_values(cur, sql, [(v,) for v in unique_vals], page_size=1000)
    return len(unique_vals)


def load_dim_datum(cur, year_month_pairs: list[tuple[int, int]]):
    """
    Loads dim_datum using the first day of the month as datum (YYYY-MM-01).
    This matches your monthly grain while keeping your existing dim_datum table.
    """
    unique = sorted({(int(y), int(m)) for (y, m) in year_month_pairs if pd.notna(y) and pd.notna(m)})
    if not unique:
        return 0

    rows = []
    for y, m in unique:
        d = date(y, m, 1)
        iso_week = int(d.isocalendar().week)
        rows.append((d, y, m, iso_week, season_from_month(m)))

    sql = """
        INSERT INTO dim_datum (datum, jahr, monat, woche, saison)
        VALUES %s
        ON CONFLICT (datum)
        DO UPDATE SET
          jahr = EXCLUDED.jahr,
          monat = EXCLUDED.monat,
          woche = EXCLUDED.woche,
          saison = EXCLUDED.saison;
    """
    execute_values(cur, sql, rows, page_size=1000)
    return len(rows)


def fetch_dim_map(cur, table: str, key_col: str, val_col: str) -> dict:
    """
    Returns mapping: value -> surrogate_key
    """
    cur.execute(f"SELECT {key_col}, {val_col} FROM {table};")
    out = {}
    for k, v in cur.fetchall():
        out[v] = int(k)
    return out


def fetch_datum_map(cur) -> dict[tuple[int, int], int]:
    """
    Returns mapping: (jahr, monat) -> datum_key
    """
    cur.execute("SELECT datum_key, jahr, monat FROM dim_datum;")
    out = {}
    for datum_key, jahr, monat in cur.fetchall():
        out[(int(jahr), int(monat))] = int(datum_key)
    return out


def require_columns(df: pd.DataFrame, cols: list[str], name: str):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}. Found: {list(df.columns)}")


# =========================
# Main
# =========================
def main():
    # ---- Files exist? ----
    if not AKTIN_CSV.exists():
        raise FileNotFoundError(f"AKTIN CSV not found: {AKTIN_CSV}")
    if not WEATHER_CSV.exists():
        raise FileNotFoundError(f"Weather CSV not found: {WEATHER_CSV}")

    aktin = pd.read_csv(AKTIN_CSV)
    weather = pd.read_csv(WEATHER_CSV)

    # ---- Validate columns ----
    require_columns(
        aktin,
        [
            "year", "month", "syndrome", "age_group", "ed_type",
            "relative_cases_avg", "relative_cases_7day_ma_avg",
            "expected_value_avg", "expected_lowerbound_avg", "expected_upperbound_avg",
            "ed_count_sum",
        ],
        "aktin_monthly.csv"
    )
    require_columns(
        weather,
        ["year", "month", "temperature_mean", "precipitation", "sunshine_duration"],
        "weather_monthly_de.csv"
    )

    # ---- Normalize & types ----
    for c in ["syndrome", "age_group", "ed_type"]:
        aktin[c] = aktin[c].astype(str).str.strip()

    aktin["year"] = pd.to_numeric(aktin["year"], errors="coerce").astype("Int64")
    aktin["month"] = pd.to_numeric(aktin["month"], errors="coerce").astype("Int64")
    aktin = aktin.dropna(subset=["year", "month"])

    weather["year"] = pd.to_numeric(weather["year"], errors="coerce").astype("Int64")
    weather["month"] = pd.to_numeric(weather["month"], errors="coerce").astype("Int64")
    weather = weather.dropna(subset=["year", "month"])

    # ---- Join weather to aktin (month-level) ----
    merged = aktin.merge(weather, on=["year", "month"], how="left")

    # ---- DB load ----
    conn = connect()
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            ensure_constraints(cur)

            # 1) Upsert dimensions
            n_syn = upsert_dim_text(cur, "dim_syndrom", "bezeichnung", merged["syndrome"].tolist())
            n_age = upsert_dim_text(cur, "dim_altersgruppe", "altersgruppe", merged["age_group"].tolist())
            n_ed  = upsert_dim_text(cur, "dim_edtype", "typ", merged["ed_type"].tolist())
            n_dt  = load_dim_datum(cur, merged[["year", "month"]].itertuples(index=False, name=None))

            # 2) Build key maps
            syndrom_map = fetch_dim_map(cur, "dim_syndrom", "syndrom_key", "bezeichnung")
            alters_map = fetch_dim_map(cur, "dim_altersgruppe", "altersgruppe_key", "altersgruppe")
            edtype_map = fetch_dim_map(cur, "dim_edtype", "edtype_key", "typ")
            datum_map = fetch_datum_map(cur)

            # 3) Prepare fact rows (skip rows with missing keys)
            fact_rows = []
            skipped = 0

            for _, r in merged.iterrows():
                y = int(r["year"])
                m = int(r["month"])

                datum_key = datum_map.get((y, m))
                syndrom_key = syndrom_map.get(r["syndrome"])
                alters_key = alters_map.get(r["age_group"])
                edtype_key = edtype_map.get(r["ed_type"])

                if datum_key is None or syndrom_key is None or alters_key is None or edtype_key is None:
                    skipped += 1
                    continue

                fact_rows.append((
                    datum_key,
                    syndrom_key,
                    alters_key,
                    edtype_key,
                    float(r["relative_cases_avg"]) if pd.notna(r["relative_cases_avg"]) else None,
                    float(r["relative_cases_7day_ma_avg"]) if pd.notna(r["relative_cases_7day_ma_avg"]) else None,
                    float(r["expected_value_avg"]) if pd.notna(r["expected_value_avg"]) else None,
                    float(r["expected_lowerbound_avg"]) if pd.notna(r["expected_lowerbound_avg"]) else None,
                    float(r["expected_upperbound_avg"]) if pd.notna(r["expected_upperbound_avg"]) else None,
                    int(r["ed_count_sum"]) if pd.notna(r["ed_count_sum"]) else None,
                    float(r["temperature_mean"]) if pd.notna(r["temperature_mean"]) else None,
                    float(r["precipitation"]) if pd.notna(r["precipitation"]) else None,
                    float(r["sunshine_duration"]) if pd.notna(r["sunshine_duration"]) else None,
                ))

            # 4) Upsert facts
            sql_fact = """
                INSERT INTO fakt_erkrankungen (
                  datum_key, syndrom_key, altersgruppe_key, edtype_key,
                  relative_cases, relative_cases_7day_ma,
                  expected_value, expected_lowerbound, expected_upperbound,
                  ed_count,
                  temperature_mean, precipitation, sunshine_duration
                ) VALUES %s
                ON CONFLICT (datum_key, syndrom_key, altersgruppe_key, edtype_key)
                DO UPDATE SET
                  relative_cases = EXCLUDED.relative_cases,
                  relative_cases_7day_ma = EXCLUDED.relative_cases_7day_ma,
                  expected_value = EXCLUDED.expected_value,
                  expected_lowerbound = EXCLUDED.expected_lowerbound,
                  expected_upperbound = EXCLUDED.expected_upperbound,
                  ed_count = EXCLUDED.ed_count,
                  temperature_mean = EXCLUDED.temperature_mean,
                  precipitation = EXCLUDED.precipitation,
                  sunshine_duration = EXCLUDED.sunshine_duration;
            """
            execute_values(cur, sql_fact, fact_rows, page_size=2000)

        conn.commit()
        print("✅ LOAD DONE")
        print(f"  - dim inserts attempted (unique values): syndrom={n_syn}, altersgruppe={n_age}, edtype={n_ed}, datum(months)={n_dt}")
        print(f"  - facts upserted: {len(fact_rows)}")
        print(f"  - rows skipped (missing keys): {skipped}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

