#!/usr/bin/env python
"""Scrape product catalog from fashion retailers."""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.registry import get_scraper, SCRAPERS, list_scrapers


def scrape_source(source: str, output_dir: Path, limit: int = None, test_mode: bool = False):
    """Scrape a single source and save to JSON."""
    print(f"\nScraping {source}...")

    scraper = get_scraper(source)
    items = scraper.scrape_all()

    # Apply limit if specified
    if limit and len(items) > limit:
        items = items[:limit]

    # Use _test suffix in test mode
    suffix = "_test" if test_mode else ""
    output_file = output_dir / f"{source}{suffix}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([item.__dict__ for item in items], f, indent=2, ensure_ascii=False)

    print(f"  Scraped {len(items)} items -> {output_file}")
    return items


def scrape_all(output_dir: Path, limit: int = None, test_mode: bool = False):
    """Scrape all available sources."""
    total = 0
    for source in SCRAPERS.keys():
        items = scrape_source(source, output_dir, limit, test_mode)
        total += len(items)
    return total


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape fashion product catalogs")
    parser.add_argument(
        "--source", "-s",
        choices=list_scrapers(),
        help="Specific source to scrape (default: all)"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/catalog",
        help="Output directory (default: data/catalog)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of items to scrape"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run in test mode (scrape only 10 items)"
    )
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set limit for test mode
    limit = args.limit
    if args.test:
        limit = 10
        print("Running in test mode (limit=10)...")

    if args.source:
        items = scrape_source(args.source, output_dir, limit, args.test)
        if items:
            print(f"\nFirst item:")
            for key, value in items[0].__dict__.items():
                val_str = str(value)
                if len(val_str) > 80:
                    val_str = val_str[:77] + "..."
                print(f"    {key}: {val_str}")
    else:
        total = scrape_all(output_dir, limit, args.test)
        print(f"\nTotal items scraped: {total}")
