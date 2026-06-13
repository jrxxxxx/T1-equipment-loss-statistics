from pathlib import Path
from math import comb

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
TABLE_DIR = ROOT / "outputs" / "tables"


def two_sided_binom_pvalue(k: int, n: int, p: float = 0.5) -> float:
    observed = comb(n, k) * (p**k) * ((1 - p) ** (n - k))
    total = 0.0
    for i in range(n + 1):
        prob = comb(n, i) * (p**i) * ((1 - p) ** (n - i))
        if prob <= observed + 1e-15:
            total += prob
    return min(1.0, total)


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(PROCESSED_DIR / "losses_clean.csv", parse_dates=["date"])
    counts = df["side"].value_counts()

    russia = int(counts.get("Russia", 0))
    ukraine = int(counts.get("Ukraine", 0))
    total = russia + ukraine
    if total == 0:
        raise ValueError("No Russia/Ukraine observations available.")

    if russia == 0 or ukraine == 0:
        result = pd.DataFrame(
            [
                {
                    "russia_count": russia,
                    "ukraine_count": ukraine,
                    "total_count": total,
                    "status": "skipped",
                    "reason": "Conditional two-side Poisson test requires observations from both sides.",
                }
            ]
        )
        result.to_csv(TABLE_DIR / "poisson_equal_rate_test.csv", index=False, encoding="utf-8-sig")
        print(result.to_string(index=False))
        return

    # Conditional test for equal Poisson rates when exposure time is equal.
    p_value = two_sided_binom_pvalue(russia, total, p=0.5)

    result = pd.DataFrame(
        [
            {
                "russia_count": russia,
                "ukraine_count": ukraine,
                "total_count": total,
                "null_hypothesis": "lambda_Russia = lambda_Ukraine",
                "conditional_p_value": p_value,
                "reject_5_percent": p_value < 0.05,
            }
        ]
    )
    result.to_csv(TABLE_DIR / "poisson_equal_rate_test.csv", index=False, encoding="utf-8-sig")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
