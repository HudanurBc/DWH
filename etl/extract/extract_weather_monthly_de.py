import pandas as pd
import requests
from pathlib import Path
from io import StringIO

BASE_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/"
    "regional_averages_DE/monthly/air_temperature_mean/"
)
OUT_RAW_DIR = Path("data/raw/dwd_air_temperature_mean_monthly")
OUT_PROCESSED = Path("data/processed/weather_monthly_de.csv")


def _download_text(url: str) -> str:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.text


def _parse_dwd_table(text: str) -> pd.DataFrame:
    """
    DWD-Dateien enthalten manchmal Kopfzeilen. Wir suchen die Zeile,
    die mit 'Jahr;Monat' beginnt und lesen ab dort als CSV (sep=';').
    """
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("Jahr;Monat"):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Konnte Header 'Jahr;Monat' nicht finden. Format hat sich evtl. geändert.")

    csv_text = "\n".join(lines[header_idx:])
    df = pd.read_csv(StringIO(csv_text), sep=";", engine="python")

    # Spaltennamen trimmen
    df.columns = [c.strip() for c in df.columns]

    # Manche Dateien haben eine letzte leere Spalte wegen trailing ';'
    df = df.loc[:, [c for c in df.columns if c != "" and not c.startswith("Unnamed")]]

    return df


def main():
    OUT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PROCESSED.parent.mkdir(parents=True, exist_ok=True)

    all_months = []

    for m in range(1, 13):
        mm = f"{m:02d}"
        filename = f"regional_averages_tm_{mm}.txt"
        url = BASE_URL + filename

        print(f"Downloading: {url}")
        text = _download_text(url)

        # Raw speichern
        raw_path = OUT_RAW_DIR / filename
        raw_path.write_text(text, encoding="utf-8")

        # Parsen
        df = _parse_dwd_table(text)

        # Nur Deutschland-Spalte extrahieren
        if "Deutschland" not in df.columns:
            raise ValueError(f"'Deutschland' Spalte nicht gefunden in {filename}. Verfügbare Spalten: {df.columns}")

        df_de = df[["Jahr", "Monat", "Deutschland"]].copy()
        df_de = df_de.rename(columns={"Jahr": "year", "Monat": "month", "Deutschland": "temperature_mean"})

        # Werte bereinigen: Whitespace, Dezimalkomma, leere Strings → NaN
        df_de["temperature_mean"] = (
            df_de["temperature_mean"]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)
        )
        df_de["temperature_mean"] = pd.to_numeric(df_de["temperature_mean"], errors="coerce")

        # year/month als int
        df_de["year"] = pd.to_numeric(df_de["year"], errors="coerce").astype("Int64")
        df_de["month"] = pd.to_numeric(df_de["month"], errors="coerce").astype("Int64")

        # Nur valide Zeilen behalten
        df_de = df_de.dropna(subset=["year", "month", "temperature_mean"])

        all_months.append(df_de)

    # Zusammenführen
    weather = pd.concat(all_months, ignore_index=True)

    # Duplikate entfernen (falls Monate mehrfach vorkommen)
    weather = weather.drop_duplicates(subset=["year", "month"], keep="last")

    # Sortieren
    weather = weather.sort_values(["year", "month"]).reset_index(drop=True)

    # Schreiben
    weather.to_csv(OUT_PROCESSED, index=False)

    print(f"\n Raw files saved under: {OUT_RAW_DIR}")
    print(f" Processed Germany monthly weather saved to: {OUT_PROCESSED}")
    print(f"Rows: {len(weather)}  |  Years: {weather['year'].min()}–{weather['year'].max()}")


if __name__ == "__main__":
    main()

