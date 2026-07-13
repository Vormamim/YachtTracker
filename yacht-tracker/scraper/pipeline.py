"""Data model + CSV append pipeline. Source-agnostic, fully testable."""
import csv
import hashlib
from dataclasses import dataclass, asdict, fields
from datetime import date
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "data" / "listings.csv"


@dataclass
class Listing:
    run_date: str
    listing_id: str
    title: str
    price_eur: int | None
    length_ft: float | None
    year: int | None
    url: str
    source: str
    region: str = ""

    @staticmethod
    def make_id(url: str) -> str:
        return hashlib.sha1(url.strip().lower().encode()).hexdigest()[:12]


def in_range(length_ft: float | None, lo: float = 38.0, hi: float = 43.0) -> bool:
    return length_ft is not None and lo <= length_ft <= hi


def append_snapshot(listings: list[Listing], csv_path: Path = CSV_PATH) -> int:
    """Append today's rows. Skips (run_date, listing_id) pairs already present,
    so a re-run on the same day is idempotent. Returns rows written."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    cols = [f.name for f in fields(Listing)]

    seen: set[tuple[str, str]] = set()
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add((row["run_date"], row["listing_id"]))

    new_file = not csv_path.exists()
    written = 0
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if new_file:
            w.writeheader()
        for l in listings:
            key = (l.run_date, l.listing_id)
            if key in seen:
                continue
            seen.add(key)
            w.writerow(asdict(l))
            written += 1
    return written


def today() -> str:
    return date.today().isoformat()
