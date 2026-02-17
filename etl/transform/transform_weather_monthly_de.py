import pandas as pd
from pathlib import Path
from io import StringIO

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEMP_DIR = PROJECT_ROOT / "data/raw/dwd/air_temperature_mean"
PRECIP_DIR = PROJECT_ROOT / "data/raw/dwd/precipitation"
SUN_DIR = PROJECT_ROOT / "data/raw/dwd/sunshine_duration"

OUT_PATH = PROJECT_ROOT / "data/processed/weather_monthly_de.csv"


def _parse_dwd_table_text(text: str) -> pd.DataFrame:
    """Findet die Header-Zeile 'Jahr;Monat' und liest ab dort als ';'-CSV."""
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("Jahr;Monat"):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Header 'Jahr;Monat' nicht gefunden (Format evtl. geändert).")

    df = pd.read_csv(StringIO("\n".join(lines[header_idx:])), sep=";", engine="python")
    df.columns = [c.strip() for c in df.columns]

    # Trailing ';' erzeugt manchmal leere Spalte
    df = df.loc[:, [c for c in df.columns if c and not c.startswith("Unnamed")]]
    return df


def _load_series(folder: Path, pattern: str, value_col: str) -> pd.DataFrame:
    files = sorted(folder.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Keine Dateien gefunden: {folder} pattern={pattern}")

    parts = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        df = _parse_dwd_table_text(text)

        if "Deutschland" not in df.columns:
            raise ValueError(f"'Deutschland' nicht gefunden in {p.name}")

        out = df[["Jahr", "Monat", "Deutschland"]].copy()
        out = out.rename(columns={"Jahr": "year", "Monat": "month", "Deutschland": value_col})

        # Dezimalkomma + Typen
        out[value_col] = (
            out[value_col].astype(str).str.strip().str.replace(",", ".", regex=False)
        )
        out[value_col] = pd.to_numeric(out[value_col], errors="coerce")

        out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
        out["month"] = pd.to_numeric(out["month"], errors="coerce").astype("Int64")

        out = out.dropna(subset=["year", "month", value_col])
        parts.append(out)

    df_all = pd.concat(parts, ignore_index=True)
    df_all = df_all.drop_duplicates(subset=["year", "month"], keep="last")
    df_all = df_all.sort_values(["year", "month"]).reset_index(drop=True)
    return df_all


def main():
    temp = _load_series(TEMP_DIR, "regional_averages_tm_*.txt", "temperature_mean")
    precip = _load_series(PRECIP_DIR, "regional_averages_rr_*.txt", "precipitation")
    sun = _load_series(SUN_DIR, "regional_averages_sd_*.txt", "sunshine_duration")

    weather = temp.merge(precip, on=["year", "month"], how="inner").merge(sun, on=["year", "month"], how="inner")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weather.to_csv(OUT_PATH, index=False)

    print(f"Saved processed weather to {OUT_PATH}")
    print(weather.head())
    print(f"Rows: {len(weather)} | Years: {int(weather['year'].min())}-{int(weather['year'].max())}")

if __name__ == "__main__":
    main()

