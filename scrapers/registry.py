try:
    from .raven import RavenScraper
    from .terminalx import TerminalXScraper
    from .matimli import MatimliScraper
except ImportError:
    from raven import RavenScraper
    from terminalx import TerminalXScraper
    from matimli import MatimliScraper

SCRAPERS = {
    "raven": RavenScraper,
    "terminalx": TerminalXScraper,
    "matimli": MatimliScraper,
}


def get_scraper(name: str):
    """Get a scraper instance by name."""
    if name not in SCRAPERS:
        raise KeyError(f"Unknown scraper: {name}. Available: {list(SCRAPERS.keys())}")
    return SCRAPERS[name]()


def list_scrapers() -> list[str]:
    """List all available scraper names."""
    return list(SCRAPERS.keys())


if __name__ == "__main__":
    print("Testing scraper registry...")

    # Test listing scrapers
    print(f"\nAvailable scrapers: {list_scrapers()}")

    # Test getting scraper
    scraper = get_scraper("raven")
    print(f"\nGot scraper: {scraper.__class__.__name__}")
    print(f"  SOURCE: {scraper.SOURCE}")
    print(f"  BASE_URL: {scraper.BASE_URL}")

    # Test error handling
    try:
        get_scraper("unknown")
    except KeyError as e:
        print(f"\nKeyError raised for unknown scraper: {e}")

    print("\nTest passed!")
