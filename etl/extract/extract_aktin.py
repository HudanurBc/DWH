import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # → DWH

AKTIN_URL = "https://raw.githubusercontent.com/robert-koch-institut/Daten_der_Notaufnahmesurveillance/main/Notaufnahmesurveillance_Zeitreihen_Syndrome.tsv"

RAW_OUT = PROJECT_ROOT / "data/raw/aktin/Notaufnahmesurveillance_Zeitreihen_Syndrome.tsv"

def main():
    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(AKTIN_URL, timeout=60)
    r.raise_for_status()
    RAW_OUT.write_bytes(r.content)
    print(f"Saved raw AKTIN to {RAW_OUT} ({len(r.content)} bytes)")

if __name__ == "__main__":
    main()

