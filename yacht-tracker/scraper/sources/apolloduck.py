"""Apollo Duck adapter — sailing yachts located in Greece, 38–43 ft.

Verified against the live site 2026-07-13: the country portals
(greece.apolloduck.com) no longer resolve; search goes through
/listings.phtml with rid (country), cid=2 (Sailing Yachts),
minl/maxl in centimetres, and offset-based pagination via `next`.
Results render as div._FeatureAdPanel cards with a _PanelSpecTable
holding Year / Length / Location / Price rows.
"""
from bs4 import BeautifulSoup
from .base import BaseSource, parse_price_eur, parse_length_ft, parse_year
from ..pipeline import Listing, in_range, today

PAGE_SIZE = 50
SEARCH_URL = (
    "https://www.apolloduck.com/listings.phtml"
    "?view=1&layout=1&fx=EUR&rid=gr&cid=2&type=1"
    "&minl=1158.24&maxl=1310.64"  # 38–43 ft in cm
    "&sort=0&limit={limit}&next={offset}"
)
CARD = "div._FeatureAdPanel"
TITLE = "a._FeatureTitle"
LINK = "a[href*='/boat/']"
PRICE = "span._FeaturePrice"


class ApolloDuck(BaseSource):
    name = "apolloduck"

    def fetch(self, max_pages: int = 5, debug: bool = False) -> list[Listing]:
        out, run, seen = [], today(), set()
        for page in range(max_pages):
            url = SEARCH_URL.format(limit=PAGE_SIZE, offset=page * PAGE_SIZE)
            soup = BeautifulSoup(self.get(url).text, "html.parser")
            cards = soup.select(CARD)
            if debug and cards:
                print(f"--- {self.name} first card HTML ---\n{cards[0].prettify()[:3000]}")
            if not cards:
                break
            for c in cards:
                a = c.select_one(LINK)
                t = c.select_one(TITLE)
                if not a or not a.get("href"):
                    continue
                url = a["href"]
                if url.startswith("/"):
                    url = "https://www.apolloduck.com" + url
                lid = Listing.make_id(url)
                if lid in seen:  # featured ads repeat across pages
                    continue
                seen.add(lid)
                specs = {
                    row.select_one("td._PanelSpecLabel").get_text(strip=True).rstrip(":"):
                    row.select_one("td._PanelSpecData").get_text(" ", strip=True)
                    for row in c.select("table._PanelSpecTable tr")
                    if row.select_one("td._PanelSpecLabel") and row.select_one("td._PanelSpecData")
                }
                length = parse_length_ft(specs.get("Length", ""))
                if not in_range(length):
                    continue
                price_el = c.select_one(PRICE)
                price_text = specs.get("Price") or (price_el.get_text(" ", strip=True) if price_el else "")
                out.append(Listing(
                    run_date=run,
                    listing_id=lid,
                    title=(t.get_text(strip=True) if t else "")[:120],
                    price_eur=parse_price_eur(price_text),
                    length_ft=length,
                    year=parse_year(specs.get("Year", "")),
                    url=url,
                    source=self.name,
                ))
        return out
