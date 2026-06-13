from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
FIGURE_DIR = ROOT / "outputs" / "figures"
TABLE_DIR = ROOT / "outputs" / "tables"


def write_bar_svg(rows: list[tuple[str, int]], path: Path, title: str) -> None:
    width, height = 900, max(280, 70 + 36 * len(rows))
    left, right, top = 220, 40, 50
    bar_h, gap = 22, 14
    max_value = max((value for _, value in rows), default=1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial, sans-serif;font-size:13px}.title{font-size:20px;font-weight:bold}.bar{fill:#3b82f6}.label{fill:#111827}.value{fill:#374151}</style>',
        f'<text class="title" x="{left}" y="28" text-anchor="middle">{title}</text>',
    ]
    for i, (label, value) in enumerate(rows):
        y = top + i * (bar_h + gap)
        bar_w = int((width - left - right - 90) * value / max_value)
        parts.append(f'<text class="label" x="{left - 10}" y="{y + 16}" text-anchor="end">{label}</text>')
        parts.append(f'<rect class="bar" x="{left}" y="{y}" width="{bar_w}" height="{bar_h}" />')
        parts.append(f'<text class="value" x="{left + bar_w + 8}" y="{y + 16}">{value}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_line_svg(series_by_side: dict[str, list[tuple[pd.Timestamp, int]]], path: Path, title: str) -> None:
    width, height = 1000, 420
    left, right, top, bottom = 60, 30, 50, 50
    all_dates = [date for series in series_by_side.values() for date, _ in series]
    all_values = [value for series in series_by_side.values() for _, value in series]
    if not all_dates:
        return
    min_date, max_date = min(all_dates), max(all_dates)
    max_value = max(all_values) if all_values else 1
    span_days = max(1, (max_date - min_date).days)

    def point(date: pd.Timestamp, value: int) -> tuple[float, float]:
        x = left + (width - left - right) * (date - min_date).days / span_days
        y = height - bottom - (height - top - bottom) * value / max_value
        return x, y

    colors = {"Russia": "#ef4444", "Ukraine": "#2563eb"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial, sans-serif;font-size:13px}.title{font-size:20px;font-weight:bold}.axis{stroke:#9ca3af}.line{fill:none;stroke-width:2}</style>',
        f'<text class="title" x="{width / 2}" y="28" text-anchor="middle">{title}</text>',
        f'<line class="axis" x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" />',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" />',
        f'<text x="{left}" y="{height-20}" text-anchor="middle">{min_date.date()}</text>',
        f'<text x="{width-right}" y="{height-20}" text-anchor="end">{max_date.date()}</text>',
        f'<text x="{left-8}" y="{top+5}" text-anchor="end">{max_value}</text>',
    ]
    legend_x = width - right - 170
    for i, (side, series) in enumerate(series_by_side.items()):
        color = colors.get(side, "#111827")
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(d, v) for d, v in series))
        parts.append(f'<polyline class="line" stroke="{color}" points="{points}" />')
        parts.append(f'<rect x="{legend_x}" y="{top + i * 22}" width="14" height="14" fill="{color}" />')
        parts.append(f'<text x="{legend_x + 20}" y="{top + 12 + i * 22}">{side}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    data_path = PROCESSED_DIR / "losses_clean.csv"
    if not data_path.exists():
        raise FileNotFoundError("Run src/01_load_clean_data.py first.")

    df = pd.read_csv(data_path, parse_dates=["date"])

    total_by_side = df.groupby("side").size().reset_index(name="loss_count")
    total_by_side.to_csv(TABLE_DIR / "total_by_side.csv", index=False, encoding="utf-8-sig")
    write_bar_svg(
        list(total_by_side.sort_values("loss_count", ascending=False).itertuples(index=False, name=None)),
        FIGURE_DIR / "total_by_side.svg",
        "Total Verified Equipment Losses by Side",
    )

    type_side = (
        df.groupby(["equipment_type", "side"])
        .size()
        .reset_index(name="loss_count")
        .sort_values("loss_count", ascending=False)
    )
    type_side.to_csv(TABLE_DIR / "losses_by_type_side.csv", index=False, encoding="utf-8-sig")

    top_types = type_side.groupby("equipment_type")["loss_count"].sum().nlargest(12).index
    plot_df = type_side[type_side["equipment_type"].isin(top_types)]
    type_totals = (
        plot_df.groupby("equipment_type")["loss_count"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    write_bar_svg(
        list(type_totals.itertuples(index=False, name=None)),
        FIGURE_DIR / "losses_by_type_side.svg",
        "Verified Losses by Equipment Type",
    )

    weekly = pd.read_csv(PROCESSED_DIR / "weekly_losses.csv", parse_dates=["date"])
    series_by_side = {
        side: list(group[["date", "loss_count"]].itertuples(index=False, name=None))
        for side, group in weekly.groupby("side")
    }
    write_line_svg(series_by_side, FIGURE_DIR / "weekly_losses.svg", "Weekly Verified Equipment Losses")

    print("Saved descriptive tables and figures.")


if __name__ == "__main__":
    main()
