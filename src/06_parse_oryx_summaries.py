from html import unescape
from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


FILES = {
    "Russia": RAW_DIR / "oryx_russia.html",
    "Ukraine": RAW_DIR / "oryx_ukraine.html",
}


HEADING_RE = re.compile(
    r"<h3[^>]*>\s*(.*?)\s*</h3>",
    flags=re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
COUNT_RE = re.compile(
    r"^(?P<category>.+?)\s*[-–]?\s*\((?P<total>\d+),\s*of which destroyed:\s*(?P<destroyed>\d+),\s*damaged:\s*(?P<damaged>\d+),\s*abandoned:\s*(?P<abandoned>\d+),\s*captured:\s*(?P<captured>\d+)\)",
    flags=re.IGNORECASE,
)
SIDE_TOTAL_RE = re.compile(
    r"^(?P<side>Russia|Ukraine)\s*[-–]\s*(?P<total>\d+),\s*of which:\s*destroyed:\s*(?P<destroyed>\d+),\s*damaged:\s*(?P<damaged>\d+),\s*abandoned:\s*(?P<abandoned>\d+),\s*captured:\s*(?P<captured>\d+)",
    flags=re.IGNORECASE,
)


def clean_heading(html: str) -> str:
    text = TAG_RE.sub("", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_file(side: str, path: Path) -> list[dict[str, object]]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    rows = []
    for match in HEADING_RE.finditer(html):
        heading = clean_heading(match.group(1))
        side_match = SIDE_TOTAL_RE.search(heading)
        count_match = COUNT_RE.search(heading)

        if side_match:
            row = side_match.groupdict()
            row["side"] = side
            row["category"] = "Total"
        elif count_match:
            row = count_match.groupdict()
            row["side"] = side
        else:
            continue

        for key in ["total", "destroyed", "damaged", "abandoned", "captured"]:
            row[key] = int(row[key])
        rows.append(row)
    return rows


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for side, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}. Download Oryx HTML pages first.")
        rows.extend(parse_file(side, path))

    summary = pd.DataFrame(rows)
    summary = summary[["side", "category", "total", "destroyed", "damaged", "abandoned", "captured"]]
    summary.to_csv(PROCESSED_DIR / "oryx_side_category_summary.csv", index=False, encoding="utf-8-sig")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

