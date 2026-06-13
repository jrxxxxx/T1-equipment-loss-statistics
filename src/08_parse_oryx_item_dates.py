from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

FILES = {
    "Russia": RAW_DIR / "oryx_russia.html",
    "Ukraine": RAW_DIR / "oryx_ukraine.html",
}

H3_RE = re.compile(r"<h3[^>]*>(.*?)</h3>", flags=re.I | re.S)
A_RE = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>\s*\((.*?)\)\s*</a>', flags=re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub("", value))).strip()


def infer_status(label: str) -> str | None:
    text = label.lower()
    if "destroy" in text:
        return "destroyed"
    if "damag" in text:
        return "damaged"
    if "abandon" in text:
        return "abandoned"
    if "captur" in text:
        return "captured"
    return None


def infer_item_count(label: str) -> int:
    nums = [int(x) for x in re.findall(r"\d+", label)]
    if " and " in label.lower() and len(nums) >= 2:
        return len(nums)
    return 1


def parse_candidate(parts: tuple[int, int, int], order: str) -> date | None:
    a, b, c = parts
    try:
        if order == "ymd":
            y, m, d = a, b, c
        elif order == "dmy":
            d, m, y = a, b, c
        else:
            m, d, y = a, b, c
        if y < 100:
            y += 2000
        if 2022 <= y <= 2026:
            return date(y, m, d)
    except ValueError:
        return None
    return None


def infer_date_from_url(url: str) -> date | None:
    name = unquote(Path(urlparse(url).path).name)
    candidates: list[date] = []

    for y, m, d in re.findall(r"(?<!\d)(20\d{2})[-_](\d{1,2})[-_](\d{1,2})(?!\d)", name):
        parsed = parse_candidate((int(y), int(m), int(d)), "ymd")
        if parsed:
            candidates.append(parsed)

    for a, b, y in re.findall(r"(?<!\d)(\d{1,2})[-_](\d{1,2})[-_](20\d{2}|\d{2})(?!\d)", name):
        a_i, b_i, y_i = int(a), int(b), int(y)
        if b_i > 12:
            parsed = parse_candidate((a_i, b_i, y_i), "mdy")
        elif a_i > 12:
            parsed = parse_candidate((a_i, b_i, y_i), "dmy")
        else:
            parsed = parse_candidate((a_i, b_i, y_i), "dmy")
        if parsed:
            candidates.append(parsed)

    return candidates[-1] if candidates else None


def parse_side(side: str, path: Path) -> list[dict[str, object]]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    headings = list(H3_RE.finditer(html))
    rows = []
    for i, heading in enumerate(headings):
        category = clean_text(heading.group(1)).split("(")[0].strip()
        start = heading.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(html)
        block = html[start:end]
        for href, label_html in A_RE.findall(block):
            label = clean_text(label_html)
            status = infer_status(label)
            event_date = infer_date_from_url(href)
            if not status or not event_date:
                continue
            rows.append(
                {
                    "side": side,
                    "date": event_date.isoformat(),
                    "category": category,
                    "status": status,
                    "count": infer_item_count(label),
                    "source_url": href,
                    "source_label": label,
                }
            )
    return rows


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for side, path in FILES.items():
        rows.extend(parse_side(side, path))

    items = pd.DataFrame(rows)
    items.to_csv(PROCESSED_DIR / "oryx_item_dates_inferred.csv", index=False, encoding="utf-8-sig")

    daily = (
        items.groupby(["date", "side"])["count"]
        .sum()
        .reset_index(name="loss_count")
        .sort_values(["date", "side"])
    )
    daily.to_csv(PROCESSED_DIR / "oryx_daily_losses_inferred.csv", index=False, encoding="utf-8-sig")

    coverage = (
        items.groupby("side")["count"]
        .sum()
        .reset_index(name="parsed_item_count_with_inferred_date")
    )
    coverage.to_csv(PROCESSED_DIR / "oryx_inferred_date_coverage.csv", index=False, encoding="utf-8-sig")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()

