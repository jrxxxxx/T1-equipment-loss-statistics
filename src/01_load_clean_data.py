from pathlib import Path

import pandas as pd
import sys


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


DATE_CANDIDATES = ["date", "loss_date", "day", "timestamp", "created_at"]
SIDE_CANDIDATES = ["side", "country", "belligerent", "actor", "army", "force", "owner", "lost_by"]
TYPE_CANDIDATES = ["equipment_type", "type", "category", "equipment", "vehicle_type"]
STATUS_CANDIDATES = ["status", "loss_type", "outcome", "state"]


def find_column(columns: list[str], candidates: list[str]) -> str | None:
    lowered = {col.lower().strip(): col for col in columns}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]

    for col in columns:
        key = col.lower().strip()
        if any(candidate in key for candidate in candidates):
            return col
    return None


def normalize_side(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if "russia" in text or text in {"ru", "rus", "russian"}:
        return "Russia"
    if "ukraine" in text or text in {"ua", "ukr", "ukrainian"}:
        return "Ukraine"
    return str(value).strip()


def load_raw_data() -> pd.DataFrame:
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {RAW_DIR}. Put Kaggle CSV files in data/raw/ first."
        )

    frames = []
    for csv_path in csv_files:
        frame = pd.read_csv(csv_path)
        frame["source_file"] = csv_path.name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw_data()

    date_col = find_column(list(raw.columns), DATE_CANDIDATES)
    side_col = find_column(list(raw.columns), SIDE_CANDIDATES)
    type_col = find_column(list(raw.columns), TYPE_CANDIDATES)
    status_col = find_column(list(raw.columns), STATUS_CANDIDATES)

    print("Detected columns:")
    print(f"date:   {date_col}")
    print(f"side:   {side_col}")
    print(f"type:   {type_col}")
    print(f"status: {status_col}")

    missing = [
        name
        for name, col in {
            "date": date_col,
            "side": side_col,
            "equipment_type": type_col,
        }.items()
        if col is None
    ]
    if missing:
        raise ValueError(
            "Could not detect required columns: "
            + ", ".join(missing)
            + ". Run 00_inspect_raw_data.py and update candidate names in this script."
        )

    clean = pd.DataFrame()
    clean["date"] = pd.to_datetime(raw[date_col], errors="coerce").dt.date
    clean["side"] = raw[side_col].map(normalize_side)
    clean["equipment_type"] = raw[type_col].astype(str).str.strip()
    clean["status"] = raw[status_col].astype(str).str.strip() if status_col else "unknown"
    clean["source_file"] = raw["source_file"]

    clean = clean.dropna(subset=["date", "side", "equipment_type"])
    clean = clean[clean["side"].isin(["Russia", "Ukraine"])]
    clean["date"] = pd.to_datetime(clean["date"])

    clean_path = PROCESSED_DIR / "losses_clean.csv"
    clean.to_csv(clean_path, index=False, encoding="utf-8-sig")

    daily = (
        clean.groupby(["date", "side"])
        .size()
        .reset_index(name="loss_count")
        .sort_values(["date", "side"])
    )
    daily.to_csv(PROCESSED_DIR / "daily_losses.csv", index=False, encoding="utf-8-sig")

    weekly = (
        clean.set_index("date")
        .groupby("side")
        .resample("W")
        .size()
        .reset_index(name="loss_count")
        .sort_values(["date", "side"])
    )
    weekly.to_csv(PROCESSED_DIR / "weekly_losses.csv", index=False, encoding="utf-8-sig")

    print(f"Saved clean data: {clean_path}")
    print(f"Rows kept: {len(clean):,}")
    print(clean["side"].value_counts().to_string())


if __name__ == "__main__":
    main()
