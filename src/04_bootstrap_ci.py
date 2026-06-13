from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"

OBS_START = pd.Timestamp("2022-02-24")
OBS_END = pd.Timestamp("2026-06-10")


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    summary_path = PROCESSED_DIR / "oryx_side_category_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError("Run src/06_parse_oryx_summaries.py first.")

    totals = pd.read_csv(summary_path)
    totals = totals[totals["category"] == "Total"].set_index("side")
    if not {"Russia", "Ukraine"}.issubset(totals.index):
        raise ValueError("Need both Russia and Ukraine Oryx totals.")

    rng = np.random.default_rng(20260611)
    exposure_days = (OBS_END - OBS_START).days + 1
    r_count = int(totals.loc["Russia", "total"])
    u_count = int(totals.loc["Ukraine", "total"])
    r_lambda = r_count / exposure_days
    u_lambda = u_count / exposure_days
    n_boot = 10000
    stats = []
    for _ in range(n_boot):
        r_sim = rng.poisson(r_lambda * exposure_days)
        u_sim = rng.poisson(u_lambda * exposure_days)
        r_rate = r_sim / exposure_days
        u_rate = u_sim / exposure_days
        ratio = r_rate / u_rate if u_rate > 0 else np.nan
        stats.append({"russia_daily_rate": r_rate, "ukraine_daily_rate": u_rate, "rate_ratio": ratio})

    boot = pd.DataFrame(stats).dropna()
    summary = []
    for col in ["russia_daily_rate", "ukraine_daily_rate", "rate_ratio"]:
        summary.append(
            {
                "statistic": col,
                "estimate": boot[col].mean(),
                "ci_low_95": boot[col].quantile(0.025),
                "ci_high_95": boot[col].quantile(0.975),
            }
        )

    out = pd.DataFrame(summary)
    out.to_csv(TABLE_DIR / "bootstrap_ci.csv", index=False, encoding="utf-8-sig")
    boot.to_csv(TABLE_DIR / "bootstrap_samples.csv", index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
