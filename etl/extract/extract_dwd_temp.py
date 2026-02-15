import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/"
    "regional_averages_DE/monthly/air_temperature_mean/"
)
OUT_DIR = PROJECT_ROOT / "data/raw/dwd/air_temperature_mean"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for m in range(1, 13):
        mm = f"{m:02d}"
        filename = f"regional_averages_tm_{mm}.txt"
        url = BASE_URL + filename

        r = requests.get(url, timeout=60)
        r.raise_for_status()

        out_path = OUT_DIR / filename
        out_path.write_bytes(r.content)
        print(f"Saved {out_path} ({len(r.content)} bytes)")

if __name__ == "__main__":
    main()

