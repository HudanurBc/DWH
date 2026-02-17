import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # wenn Datei in DWH/etl/transform liegt
RAW_PATH = PROJECT_ROOT / "data/raw/aktin/Notaufnahmesurveillance_Zeitreihen_Syndrome.tsv"
OUT_PATH = PROJECT_ROOT / "data/processed/aktin_monthly.csv"

def main():
    df = pd.read_csv(RAW_PATH, sep="\t")

    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    monthly = (
        df.groupby(["year","month","syndrome","age_group","ed_type"], as_index=False)
          .agg(
              relative_cases_avg=("relative_cases","mean"),
              relative_cases_7day_ma_avg=("relative_cases_7day_ma","mean"),
              expected_value_avg=("expected_value","mean"),
              expected_lowerbound_avg=("expected_lowerbound","mean"),
              expected_upperbound_avg=("expected_upperbound","mean"),

              # B1: ed_count ist "Anzahl eingeschlossener Notaufnahmen pro Tag"
              # -> Monats-Interpretation sinnvoll als Durchschnitt (optional min/max)
              ed_count_avg=("ed_count", "mean"),
              ed_count_min=("ed_count", "min"),
              ed_count_max=("ed_count", "max"),
          )

    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(OUT_PATH, index=False)
    print(f"Saved processed AKTIN monthly to {OUT_PATH}")

if __name__ == "__main__":
    main()

