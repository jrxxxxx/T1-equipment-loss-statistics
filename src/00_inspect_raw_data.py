from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {RAW_DIR}")
        print("Please download the Kaggle dataset and place CSV files in data/raw/.")
        return

    for csv_path in csv_files:
        print("=" * 80)
        print(f"File: {csv_path.name}")
        df = pd.read_csv(csv_path, nrows=10)
        print(f"Columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, start=1):
            print(f"{i:02d}. {col}")
        print("\nPreview:")
        print(df.head(5).to_string(index=False).encode("utf-8", errors="replace").decode("utf-8"))


if __name__ == "__main__":
    main()
