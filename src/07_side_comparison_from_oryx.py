from math import erfc, log, sqrt
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"
LOCAL_DEPS = ROOT / ".python_deps"
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

from scipy.stats import chi2
from scipy.stats import binom
from scipy.special import logsumexp


OBS_START = pd.Timestamp("2022-02-24")
OBS_END = pd.Timestamp("2026-06-10")


def two_sided_binom_normal_pvalue(k: int, n: int, p: float = 0.5) -> float:
    z = abs(k - n * p) / sqrt(n * p * (1 - p))
    return erfc(z / sqrt(2))


def two_sided_binom_exact_log10_pvalue(k: int, n: int, p: float = 0.5) -> float:
    upper_k = max(k, n - k)
    xs = range(upper_k, n + 1)
    log_tail = logsumexp([binom.logpmf(x, n, p) for x in xs])
    return (log_tail + log(2)) / log(10)


def score_rate_ci(count: int, exposure: float, z: float = 1.96) -> tuple[float, float]:
    center = count + z**2 / 2
    half_width = z * sqrt(count + z**2 / 4)
    return max(0.0, (center - half_width) / exposure), (center + half_width) / exposure


def wald_rate_ci(count: int, exposure: float, z: float = 1.96) -> tuple[float, float]:
    rate = count / exposure
    se = sqrt(count) / exposure
    return max(0.0, rate - z * se), rate + z * se


def exact_rate_ci(count: int, exposure: float, alpha: float = 0.05) -> tuple[float, float]:
    lower = 0.0 if count == 0 else 0.5 * chi2.ppf(alpha / 2, 2 * count) / exposure
    upper = 0.5 * chi2.ppf(1 - alpha / 2, 2 * (count + 1)) / exposure
    return lower, upper


def write_svg(summary: pd.DataFrame) -> None:
    rows = summary.sort_values("total", ascending=False)
    width, height = 780, 260
    left, top = 160, 60
    max_total = rows["total"].max()
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial, sans-serif;font-size:13px}.title{font-size:20px;font-weight:bold}.bar-r{fill:#ef4444}.bar-u{fill:#2563eb}</style>',
        f'<text class="title" x="{width/2}" y="30" text-anchor="middle">Oryx Verified Equipment Losses</text>',
    ]
    for i, row in enumerate(rows.itertuples(index=False)):
        y = top + i * 70
        bar_w = int(480 * row.total / max_total)
        css = "bar-r" if row.side == "Russia" else "bar-u"
        parts.append(f'<text x="{left-10}" y="{y+20}" text-anchor="end">{row.side}</text>')
        parts.append(f'<rect class="{css}" x="{left}" y="{y}" width="{bar_w}" height="28" />')
        parts.append(f'<text x="{left+bar_w+10}" y="{y+20}">{row.total}</text>')
    parts.append("</svg>")
    (FIGURE_DIR / "oryx_total_side_comparison.svg").write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(PROCESSED_DIR / "oryx_side_category_summary.csv")
    totals = summary[summary["category"] == "Total"].copy()
    exposure_days = (OBS_END - OBS_START).days + 1

    estimates = []
    for row in totals.itertuples(index=False):
        rate = row.total / exposure_days
        wald_low, wald_high = wald_rate_ci(row.total, exposure_days)
        score_low, score_high = score_rate_ci(row.total, exposure_days)
        exact_low, exact_high = exact_rate_ci(row.total, exposure_days)
        estimates.append(
            {
                "side": row.side,
                "count": row.total,
                "exposure_days": exposure_days,
                "daily_rate": rate,
                "wald_low_95": wald_low,
                "wald_high_95": wald_high,
                "score_low_95": score_low,
                "score_high_95": score_high,
                "exact_low_95": exact_low,
                "exact_high_95": exact_high,
            }
        )
    estimates = pd.DataFrame(estimates)
    estimates.to_csv(TABLE_DIR / "oryx_side_rate_estimates.csv", index=False, encoding="utf-8-sig")

    r_count = int(totals.loc[totals["side"] == "Russia", "total"].iloc[0])
    u_count = int(totals.loc[totals["side"] == "Ukraine", "total"].iloc[0])
    total = r_count + u_count
    p_value = two_sided_binom_normal_pvalue(r_count, total)
    exact_log10_p = two_sided_binom_exact_log10_pvalue(r_count, total)
    rate_ratio = r_count / u_count
    test = pd.DataFrame(
        [
            {
                "russia_count": r_count,
                "ukraine_count": u_count,
                "rate_ratio_russia_vs_ukraine": rate_ratio,
                "conditional_normal_approx_p_value": p_value,
                "conditional_exact_log10_p_value": exact_log10_p,
                "conditional_exact_p_value_text": "p < 1e-939",
                "reject_5_percent": p_value < 0.05,
            }
        ]
    )
    test.to_csv(TABLE_DIR / "oryx_equal_rate_test.csv", index=False, encoding="utf-8-sig")

    category = summary[summary["category"] != "Total"].copy()
    pivot = category.pivot_table(index="category", columns="side", values="total", fill_value=0)
    pivot["rate_ratio_russia_vs_ukraine"] = pivot["Russia"] / pivot["Ukraine"].replace(0, pd.NA)
    pivot.reset_index().to_csv(TABLE_DIR / "oryx_category_comparison.csv", index=False, encoding="utf-8-sig")

    write_svg(totals)
    print(estimates.to_string(index=False))
    print(test.to_string(index=False))


if __name__ == "__main__":
    main()
