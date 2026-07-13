"""Daily run entry point.

Usage:
    python main.py                     # all regions
    python main.py --region turkey     # one region
    python main.py --region turkey --debug   # dump first card HTML for selector fixes
"""
import argparse
import sys
from scraper.pipeline import append_snapshot
from scraper.sources.apolloduck import ApolloDuck, REGIONS


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--region", choices=REGIONS, help="run one region only")
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()

    targets = [args.region] if args.region else list(REGIONS)
    all_listings, failures = [], []
    for region in targets:
        try:
            got = ApolloDuck(region).fetch(debug=args.debug)
            print(f"apolloduck/{region}: {len(got)} listings in range")
            all_listings += got
        except Exception as e:
            print(f"apolloduck/{region}: FAILED — {e}", file=sys.stderr)
            failures.append(region)

    n = append_snapshot(all_listings)
    print(f"wrote {n} new rows")
    # Fail the workflow only if *every* region failed
    return 1 if failures and len(failures) == len(targets) else 0


if __name__ == "__main__":
    sys.exit(main())
