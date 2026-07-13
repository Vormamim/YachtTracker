"""boat24.com adapter — sailboats, Greece, 38–43 ft (11.6–13.1 m).

NOTE: SELECTORS ARE BEST-EFFORT and must be verified against live HTML on
first run (this was authored without live site access). Run:
    python main.py --source boat24 --debug
to dump the first result card's HTML and adjust CARD/field selectors.
"""
from bs4 import BeautifulSoup
from .base import BaseSource, parse_price_eur, parse_length_ft, parse_year
from ..pipeline import Listing, in_range, today

# Search URL: sailboats, country Greece, length 11.6–13.2 m. VERIFY params.
SEARCH_URL = (
    "https://www.boat24.com/en/sailboats/"
    "?src=boat24&whr=griechenland&lng_from=11.6&lng_to=13.2&page={page}"
)
CARD = "article"          # VERIFY: result card container
TITLE = "h2, h3"          # VERIFY
LINK = "a[href*='/en/']"  # VERIFY
PRICE = ".price, [class*='price']"   # VERIFY
SPECS = ".specs, [class*='spec'], [class*='detail']"  # VERIFY


class Boat24(BaseSource):
    name = "boat24"

    def fetch(self, max_pages: int = 5, debug: bool = False) -> list[Listing]:
        out, run = [], today()
        for page in range(1, max_pages + 1):
            soup = BeautifulSoup(self.get(SEARCH_URL.format(page=page)).text, "html.parser")
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
                    url = "https://www.boat24.com" + url
                spec_text = " ".join(el.get_text(" ", strip=True) for el in c.select(SPECS)) or c.get_text(" ", strip=True)
                price_el = c.select_one(PRICE)
                length = parse_length_ft(spec_text)
                if not in_range(length):
                    continue
                out.append(Listing(
                    run_date=run,
                    listing_id=Listing.make_id(url),
                    title=(t.get_text(strip=True) if t else "")[:120],
                    price_eur=parse_price_eur(price_el.get_text(" ", strip=True) if price_el else spec_text),
                    length_ft=length,
                    year=parse_year(spec_text),
                    url=url,
                    source=self.name,
                ))
        return out
