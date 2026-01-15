import httpx

try:
    from .base import BaseScraper, Item
except ImportError:
    from base import BaseScraper, Item


class RavenScraper(BaseScraper):
    """Scraper for raven.co.il - Israeli activewear brand (Shopify store)."""

    SOURCE = "raven"
    BASE_URL = "https://raven.co.il"

    # Hebrew category mapping for activewear
    CATEGORY_MAP = {
        # Upper body - Hebrew
        "טופ": "upper_body",
        "חולצה": "upper_body",
        "גוזיה": "upper_body",
        "קרופ": "upper_body",
        "סווטשירט": "upper_body",
        "ז'קט": "upper_body",
        # Upper body - English
        "top": "upper_body",
        "shirt": "upper_body",
        "bra": "upper_body",
        "jacket": "upper_body",
        "hoodie": "upper_body",
        # Lower body - Hebrew
        "טייץ": "lower_body",
        "מכנס": "lower_body",
        "שורט": "lower_body",
        "לגינס": "lower_body",
        # Lower body - English
        "legging": "lower_body",
        "pants": "lower_body",
        "shorts": "lower_body",
        # Full body / Sets
        "סט": "full_body",
        "set": "full_body",
        "אוברול": "full_body",
    }

    def scrape_all(self) -> list[Item]:
        items = []
        page = 1

        while True:
            resp = httpx.get(
                f"{self.BASE_URL}/products.json?limit=250&page={page}",
                timeout=30
            )
            products = resp.json().get("products", [])

            if not products:
                break

            for p in products:
                item = self._parse(p)
                if item:  # Skip items without images
                    items.append(item)
            page += 1

        return items

    def _parse(self, p: dict) -> Item | None:
        # Skip products without images
        if not p.get("images"):
            return None

        # Get price from first variant
        price = 0.0
        if p.get("variants"):
            price = float(p["variants"][0].get("price", 0))

        return Item(
            id=str(p["id"]),
            source=self.SOURCE,
            name=p["title"],
            price=price,
            currency="ILS",
            category=self.map_category(p.get("product_type", "") + " " + p.get("title", "")),
            image_url=p["images"][0]["src"],
            product_url=f"{self.BASE_URL}/products/{p['handle']}"
        )

    def map_category(self, raw: str) -> str:
        raw_lower = raw.lower()
        for key, cat in self.CATEGORY_MAP.items():
            if key in raw_lower:
                return cat
        return "upper_body"  # Default to upper_body


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/Users/ormeiri/Desktop/VTO")

    print("Testing RavenScraper (raven.co.il)...")
    scraper = RavenScraper()

    # Test category mapping
    print("\nCategory mapping tests:")
    print(f"  'טופ LIRUX' -> {scraper.map_category('טופ LIRUX')}")
    print(f"  'טייץ ארוך' -> {scraper.map_category('טייץ ארוך')}")
    print(f"  'סט ספורט' -> {scraper.map_category('סט ספורט')}")
    print(f"  'leggings' -> {scraper.map_category('leggings')}")

    # Test actual scraping
    print("\nFetching products from raven.co.il...")
    try:
        resp = httpx.get(f"{scraper.BASE_URL}/products.json?limit=5&page=1", timeout=10)
        products = resp.json().get("products", [])
        print(f"  Found {len(products)} products (limited to 5)")

        if products:
            item = scraper._parse(products[0])
            if item:
                print(f"\n  First item parsed:")
                print(f"    ID: {item.id}")
                print(f"    Name: {item.name}")
                print(f"    Price: {item.price} {item.currency}")
                print(f"    Category: {item.category}")
                print(f"    Image: {item.image_url[:60]}...")
                print(f"    URL: {item.product_url}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\nTest passed!")
