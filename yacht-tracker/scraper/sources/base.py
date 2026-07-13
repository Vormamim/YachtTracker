"""Shared scraper base: polite fetching + common field parsers."""
import re
import time
import requests

UA = "yacht-price-tracker/1.0 (personal research; contact via repo)"
DELAY_S = 2.0
M_TO_FT = 3.28084


class BaseSource:
    name = "base"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = UA
        self._last = 0.0

    def get(self, url: str, **kw) -> requests.Response:
        wait = DELAY_S - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        r = self.session.get(url, timeout=30, **kw)
        self._last = time.time()
        r.raise_for_status()
        return r

    def fetch(self) -> list:
        """Return list[Listing]. Implemented by subclasses."""
        raise NotImplementedError


def parse_price_eur(text: str) -> int | None:
    """'EUR 129.500' / '€129,500' / '129 500 €' -> 129500"""
    if not text:
        return None
    t = text.replace("\xa0", " ")
    if not re.search(r"(EUR|€)", t, re.I):
        return None  # skip non-EUR (or convert later)
    digits = re.sub(r"[^\d]", "", re.sub(r"(EUR|€)", "", t, flags=re.I))
    return int(digits) if digits else None


def parse_length_ft(text: str) -> float | None:
    """'12.40 m' -> 40.7 ft; '41 ft' -> 41.0"""
    if not text:
        return None
    m = re.search(r"([\d.,]+)\s*(m|ft|')", text, re.I)
    if not m:
        return None
    val = float(m.group(1).replace(",", "."))
    unit = m.group(2).lower()
    return round(val * M_TO_FT, 1) if unit == "m" else round(val, 1)


def parse_year(text: str) -> int | None:
    m = re.search(r"\b(19[5-9]\d|20[0-4]\d)\b", text or "")
    return int(m.group(1)) if m else None
