"""Apollo Duck adapter — sailing yachts located in Greece.

NOTE: SELECTORS ARE BEST-EFFORT — verify on first run with --debug
(authored without live site access). Apollo Duck has a Greece-specific
portal; adjust SEARCH_URL after inspecting the live site.
"""
from bs4 import BeautifulSoup
from .base import BaseSource, parse_price_eur, parse_length_ft, parse_year
from ..pipeline import Listing, in_range, today

# VERIFY: Greece sail listings index (greece.apolloduck.com or country filter)
SEARCH_URL = "https://greece.apolloduck.com/boats-for-sale/sail?page={page}"
CARD = "li.result, div.result, article"  # VERIFY
TITLE = "h2, h3, .title"                 # VERIFY
LINK = "a[href*='/boat/']"               # VERIFY
PRICE = ".price, [class*='price']"       # VERIFY


class ApolloDuck(BaseSource):
    name = "apolloduck"

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
                    url = "https://greece.apolloduck.com" + url
                text = c.get_text(" ", strip=True)
                length = parse_length_ft(text)
                if not in_range(length):
                    continue
                price_el = c.select_one(PRICE)
                out.append(Listing(
                    run_date=run,
                    listing_id=Listing.make_id(url),
                    title=(t.get_text(strip=True) if t else "")[:120],
                    price_eur=parse_price_eur(price_el.get_text(" ", strip=True) if price_el else text),
                    length_ft=length,
                    year=parse_year(text),
                    url=url,
                    source=self.name,
                ))
        return out
