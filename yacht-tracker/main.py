"""Daily run entry point.

Usage:
    python main.py                     # all sources
    python main.py --source boat24     # one source
    python main.py --source boat24 --debug   # dump first card HTML for selector fixes
"""
import argparse
import sys
from scraper.pipeline import append_snapshot
from scraper.sources.boat24 import Boat24
from scraper.sources.apolloduck import ApolloDuck

SOURCES = {s.name: s for s in (Boat24, ApolloDuck)}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=SOURCES, help="run one source only")
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()

    targets = [SOURCES[args.source]] if args.source else SOURCES.values()
    all_listings, failures = [], []
    for cls in targets:
        try:
            got = cls().fetch(debug=args.debug)
            print(f"{cls.name}: {len(got)} listings in range")
            all_listings += got
        except Exception as e:
            print(f"{cls.name}: FAILED — {e}", file=sys.stderr)
            failures.append(cls.name)

    n = append_snapshot(all_listings)
    print(f"wrote {n} new rows")
    # Fail the workflow only if *every* source failed
    return 1 if failures and len(failures) == len(list(targets)) else 0


if __name__ == "__main__":
    sys.exit(main())
