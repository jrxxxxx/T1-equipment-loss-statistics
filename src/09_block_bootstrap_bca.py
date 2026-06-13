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

from scipy.stats import norm


OBS_START = pd.Timestamp("2022-02-24")
OBS_END = pd.Timestamp("2026-06-10")
BLOCK_LENGTH = 7
N_BOOT = 10000


def make_paired_daily_series() -> pd.DataFrame:
    russia = pd.read_csv(PROCESSED_DIR / "daily_losses.csv", parse_dates=["date"])
    russia = russia[russia["side"] == "Russia"][["date", "loss_count"]]
    russia = russia.rename(columns={"loss_count": "russia"})

    ukraine = pd.read_csv(PROCESSED_DIR / "oryx_daily_losses_inferred.csv", parse_dates=["date"])
    ukraine = ukraine[ukraine["side"] == "Ukraine"][["date", "loss_count"]]
    ukraine = ukraine.rename(columns={"loss_count": "ukraine_inferred"})

    dates = pd.DataFrame({"date": pd.date_range(OBS_START, OBS_END, freq="D")})
    daily = dates.merge(russia, on="date", how="left").merge(ukraine, on="date", how="left")
    daily = daily.fillna({"russia": 0, "ukraine_inferred": 0})

    totals = pd.read_csv(PROCESSED_DIR / "oryx_side_category_summary.csv")
    totals = totals[totals["category"] == "Total"].set_index("side")["total"]

    russia_scale = float(totals["Russia"] / daily["russia"].sum())
    ukraine_scale = float(totals["Ukraine"] / daily["ukraine_inferred"].sum())

    daily["russia_scaled"] = daily["russia"] * russia_scale
    daily["ukraine_scaled"] = daily["ukraine_inferred"] * ukraine_scale
    return daily


def rate_ratio(values: np.ndarray) -> float:
    russia_total = values[:, 0].sum()
    ukraine_total = values[:, 1].sum()
    return russia_total / ukraine_total


def block_indices(n: int, block_length: int) -> list[np.ndarray]:
    return [np.arange(i, min(i + block_length, n)) for i in range(0, n, block_length)]


def bca_interval(theta_hat: float, boot: np.ndarray, jack: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    boot = np.sort(boot[np.isfinite(boot)])
    prop_less = np.mean(boot < theta_hat)
    prop_less = min(max(prop_less, 1 / (2 * len(boot))), 1 - 1 / (2 * len(boot)))
    z0 = norm.ppf(prop_less)

    jack_mean = jack.mean()
    numerator = np.sum((jack_mean - jack) ** 3)
    denominator = 6 * (np.sum((jack_mean - jack) ** 2) ** 1.5)
    acceleration = 0.0 if denominator == 0 else numerator / denominator

    qs = []
    for p in [alpha / 2, 1 - alpha / 2]:
        z = norm.ppf(p)
        adjusted = norm.cdf(z0 + (z0 + z) / (1 - acceleration * (z0 + z)))
        qs.append(float(np.quantile(boot, adjusted)))
    return qs[0], qs[1]


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    daily = make_paired_daily_series()
    values = daily[["russia_scaled", "ukraine_scaled"]].to_numpy(dtype=float)
    n = len(values)
    blocks = block_indices(n, BLOCK_LENGTH)
    n_blocks = len(blocks)
    theta_hat = rate_ratio(values)

    rng = np.random.default_rng(20260612)
    boot_stats = []
    for _ in range(N_BOOT):
        chosen = rng.integers(0, n_blocks, size=n_blocks)
        sampled = np.vstack([values[blocks[i]] for i in chosen])[:n]
        boot_stats.append(rate_ratio(sampled))
    boot = np.array(boot_stats)

    jack = []
    for i in range(n_blocks):
        keep = np.setdiff1d(np.arange(n), blocks[i])
        jack.append(rate_ratio(values[keep]))
    jack = np.array(jack)

    percentile_low, percentile_high = np.quantile(boot, [0.025, 0.975])
    bca_low, bca_high = bca_interval(theta_hat, boot, jack)

    out = pd.DataFrame(
        [
            {
                "statistic": "rate_ratio_russia_vs_ukraine",
                "estimate": theta_hat,
                "block_length_days": BLOCK_LENGTH,
                "bootstrap_replicates": N_BOOT,
                "percentile_low_95": percentile_low,
                "percentile_high_95": percentile_high,
                "bca_low_95": bca_low,
                "bca_high_95": bca_high,
                "note": "Exploratory: Russia daily data from Kaggle/WarSpotting; Ukraine daily data inferred from Oryx image filenames and scaled to Oryx totals.",
            }
        ]
    )
    out.to_csv(TABLE_DIR / "block_bootstrap_bca.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"rate_ratio": boot}).to_csv(
        TABLE_DIR / "block_bootstrap_bca_samples.csv", index=False, encoding="utf-8-sig"
    )
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()

