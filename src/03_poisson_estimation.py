from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
TABLE_DIR = ROOT / "outputs" / "tables"
LOCAL_DEPS = ROOT / ".python_deps"
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

from scipy.stats import chi2


def poisson_score_ci(count: int, exposure: float, z: float = 1.96) -> tuple[float, float]:
    # Wilson-score style interval for the Poisson mean, scaled by exposure.
    center = count + z**2 / 2
    half_width = z * np.sqrt(count + z**2 / 4)
    lower = max(0.0, (center - half_width) / exposure)
    upper = (center + half_width) / exposure
    return lower, upper


def poisson_exact_ci(count: int, exposure: float, alpha: float = 0.05) -> tuple[float, float]:
    # Garwood exact interval for a Poisson rate.
    lower = 0.0 if count == 0 else 0.5 * chi2.ppf(alpha / 2, 2 * count) / exposure
    upper = 0.5 * chi2.ppf(1 - alpha / 2, 2 * (count + 1)) / exposure
    return lower, upper


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(PROCESSED_DIR / "losses_clean.csv", parse_dates=["date"])

    days = (df["date"].max() - df["date"].min()).days + 1
    rows = []
    for side, group in df.groupby("side"):
        count = len(group)
        rate = count / days
        wald_se = np.sqrt(count) / days
        score_low, score_high = poisson_score_ci(count, days)
        exact_low, exact_high = poisson_exact_ci(count, days)
        rows.append(
            {
                "side": side,
                "count": count,
                "exposure_days": days,
                "mle_daily_rate": rate,
                "wald_low_95": max(0.0, rate - 1.96 * wald_se),
                "wald_high_95": rate + 1.96 * wald_se,
                "score_low_95": score_low,
                "score_high_95": score_high,
                "exact_low_95": exact_low,
                "exact_high_95": exact_high,
            }
        )

    result = pd.DataFrame(rows)
    result.to_csv(TABLE_DIR / "poisson_rate_estimates.csv", index=False, encoding="utf-8-sig")

    if set(result["side"]) >= {"Russia", "Ukraine"}:
        r = result.set_index("side")
        rr = r.loc["Russia", "mle_daily_rate"] / r.loc["Ukraine", "mle_daily_rate"]
        pd.DataFrame([{"rate_ratio_russia_vs_ukraine": rr}]).to_csv(
            TABLE_DIR / "rate_ratio.csv", index=False, encoding="utf-8-sig"
        )
        print(f"Rate ratio Russia / Ukraine: {rr:.4f}")

    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
