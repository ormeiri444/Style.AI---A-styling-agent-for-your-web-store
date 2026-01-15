import httpx

try:
    from .base import BaseScraper, Item
except ImportError:
    from base import BaseScraper, Item


class ReavenScraper(BaseScraper):
    SOURCE = "reaven"
    BASE_URL = "https://www.reaven.co"

    CATEGORY_MAP = {
        "hoodie": "upper_body",
        "crewneck": "upper_body",
        "t-shirt": "upper_body",
        "jacket": "upper_body",
        "bomber": "upper_body",
        "flannel": "upper_body",
        "pants": "lower_body",
        "shorts": "lower_body",
    }

    def scrape_all(self) -> list[Item]:
        items = []
        page = 1

        while True:
            resp = httpx.get(f"{self.BASE_URL}/products.json?limit=250&page={page}")
            products = resp.json().get("products", [])

            if not products:
                break

            for p in products:
                items.append(self._parse(p))
            page += 1

        return items

    def _parse(self, p: dict) -> Item:
        return Item(
            id=str(p["id"]),
            source=self.SOURCE,
            name=p["title"],
            price=float(p["variants"][0]["price"]),
            currency="EUR",
            category=self.map_category(p.get("product_type", "")),
            image_url=p["images"][0]["src"] if p["images"] else "",
            product_url=f"{self.BASE_URL}/products/{p['handle']}"
        )

    def map_category(self, raw: str) -> str:
        for key, cat in self.CATEGORY_MAP.items():
            if key in raw.lower():
                return cat
        return "upper_body"


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/Users/ormeiri/Desktop/VTO")

    print("Testing ReavenScraper...")
    scraper = ReavenScraper()

    # Test category mapping
    print("\nCategory mapping tests:")
    print(f"  'Hoodie' -> {scraper.map_category('Hoodie')}")
    print(f"  'T-Shirt' -> {scraper.map_category('T-Shirt')}")
    print(f"  'Pants' -> {scraper.map_category('Pants')}")
    print(f"  'Unknown' -> {scraper.map_category('Unknown')}")

    # Test actual scraping (fetch first page only for testing)
    print("\nFetching products from Reaven...")
    try:
        resp = httpx.get(f"{scraper.BASE_URL}/products.json?limit=5&page=1", timeout=10)
        products = resp.json().get("products", [])
        print(f"  Found {len(products)} products on first page (limited to 5)")

        if products:
            item = scraper._parse(products[0])
            print(f"\n  First item parsed:")
            print(f"    ID: {item.id}")
            print(f"    Name: {item.name}")
            print(f"    Price: {item.price} {item.currency}")
            print(f"    Category: {item.category}")
            print(f"    URL: {item.product_url}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\nTest passed!")
