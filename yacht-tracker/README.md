# Yacht Price Tracker

Daily crawl of yacht aggregators for 38–43 ft sailboats for sale in Greece.
Appends snapshot rows to `data/listings.csv` — one row per listing per day —
building a longitudinal price dataset.

## Setup
1. Push this repo to GitHub.
2. **Verify selectors** (authored blind): `pip install -r requirements.txt`,
   then `python main.py --source boat24 --debug` — it prints the first result
   card's HTML. Adjust `CARD`/`TITLE`/`LINK`/`PRICE` selectors and `SEARCH_URL`
   in `scraper/sources/*.py` until listings parse. Repeat per source.
3. Once a local run writes sane rows, the Action (`.github/workflows/daily.yml`)
   runs daily at 03:00 UTC and commits the CSV. Trigger manually via the
   Actions tab → daily-crawl → Run workflow.

## Schema
`run_date, listing_id, title, price_eur, length_ft, year, url, source`
- `listing_id` = sha1(url)[:12] — stable key; group by it for price history
- Re-runs on the same day are idempotent

## Analysis starters
```python
import pandas as pd
df = pd.read_csv("data/listings.csv", parse_dates=["run_date"])
df.groupby("listing_id")["price_eur"].agg(["first","last","count"])  # drops & days-on-market
df.assign(ppf=df.price_eur/df.length_ft).groupby(df.year//5*5)["ppf"].median()  # €/ft by era
```

## Etiquette
2 s between requests, honest UA, small page counts. Check each site's
robots.txt/ToS before relying on it long-term.

## Adding a source
Subclass `BaseSource` in `scraper/sources/`, implement `fetch()`, register in
`main.py`. If a site is JS-rendered, add Playwright for that adapter only.
