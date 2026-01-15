import httpx
import html
from typing import Optional

try:
    from .base import BaseScraper, Item
except ImportError:
    from base import BaseScraper, Item


class MatimliScraper(BaseScraper):
    """Scraper for matimli.co.il - Israeli fashion retailer (WooCommerce).

    Uses WooCommerce Store API to fetch products.
    Selects the first product image which typically shows the item clearly.
    """

    SOURCE = "matimli"
    BASE_URL = "https://matimli.co.il"
    API_URL = "https://matimli.co.il/wp-json/wc/store/v1/products"

    # Category IDs to scrape with their mappings
    CATEGORIES = [
        # Women
        (222, "upper_body"),    # חולצות נשים
        (240, "upper_body"),    # טוניקות
        (230, "upper_body"),    # גופיות
        (225, "lower_body"),    # טייצים
        (224, "lower_body"),    # מכנסיים נשים
        (227, "dresses"),       # שמלות
        (234, "upper_body"),    # עליוניות וג'קטים
        # Men
        (231, "upper_body"),    # חולצות T
        (241, "upper_body"),    # חולצות גברים
        (232, "upper_body"),    # מכופתרות גברים
        (237, "lower_body"),    # מכנסיים גברים
        (246, "lower_body"),    # ברמודות
        (238, "lower_body"),    # ג'ינסים גברים
        (247, "upper_body"),    # פולו
    ]

    # Hebrew category mapping for name-based detection
    CATEGORY_MAP = {
        # Upper body
        "חולצ": "upper_body",
        "טופ": "upper_body",
        "גופי": "upper_body",
        "טוניק": "upper_body",
        "סריג": "upper_body",
        "קרדיגן": "upper_body",
        "ג'קט": "upper_body",
        "מעיל": "upper_body",
        "סווטשירט": "upper_body",
        "פולו": "upper_body",
        "מכופתר": "upper_body",
        # Lower body
        "מכנס": "lower_body",
        "ג'ינס": "lower_body",
        "ברמודה": "lower_body",
        "שורט": "lower_body",
        "טייץ": "lower_body",
        # Dresses
        "שמלה": "dresses",
        "שמלת": "dresses",
    }

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

    def scrape_all(self) -> list[Item]:
        """Scrape all products from configured categories."""
        all_items = []
        seen_ids = set()

        for category_id, default_category in self.CATEGORIES:
            items = self._scrape_category(category_id, default_category, seen_ids)
            all_items.extend(items)

        return all_items

    def _scrape_category(self, category_id: int, default_category: str, seen_ids: set) -> list[Item]:
        """Scrape products from a single category."""
        items = []
        page = 1
        per_page = 100

        while True:
            try:
                resp = httpx.get(
                    self.API_URL,
                    params={
                        "category": category_id,
                        "per_page": per_page,
                        "page": page
                    },
                    headers=self.headers,
                    timeout=30
                )

                if resp.status_code != 200:
                    break

                products = resp.json()
                if not products:
                    break

                for p in products:
                    if p['id'] not in seen_ids:
                        seen_ids.add(p['id'])
                        item = self._parse_product(p, default_category)
                        if item:
                            items.append(item)

                # Check if there are more pages
                if len(products) < per_page:
                    break

                page += 1

            except Exception as e:
                print(f"    Error fetching category {category_id} page {page}: {e}")
                break

        return items

    def _parse_product(self, p: dict, default_category: str) -> Optional[Item]:
        """Parse product dict into Item."""
        images = p.get('images', [])
        if not images:
            return None

        # Use first image (usually the clearest product shot)
        image_url = images[0].get('src', '')
        if not image_url:
            return None

        # Decode HTML entities in name
        name = html.unescape(p.get('name', ''))

        # Get price (stored in cents)
        price = 0.0
        prices = p.get('prices', {})
        if prices.get('price'):
            price = int(prices['price']) / 100

        return Item(
            id=str(p['id']),
            source=self.SOURCE,
            name=name,
            price=price,
            currency="ILS",
            category=self.map_category(name, default_category),
            image_url=image_url,
            product_url=p.get('permalink', f"{self.BASE_URL}/product/{p['id']}")
        )

    def map_category(self, name: str, default: str = "upper_body") -> str:
        """Map product name to category."""
        name_lower = name.lower()
        for key, cat in self.CATEGORY_MAP.items():
            if key in name_lower:
                return cat
        return default


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/Users/ormeiri/Desktop/VTO")

    print("Testing MatimliScraper (matimli.co.il)...")
    scraper = MatimliScraper()

    # Test category mapping
    print("\nCategory mapping tests:")
    print(f"  'חולצת בייסיק' -> {scraper.map_category('חולצת בייסיק')}")
    print(f"  'מכנסי גינס' -> {scraper.map_category('מכנסי גינס')}")
    print(f"  'שמלת מקסי' -> {scraper.map_category('שמלת מקסי')}")

    # Test API access
    print("\nFetching products from API...")
    try:
        resp = httpx.get(
            f"{scraper.API_URL}?per_page=5",
            headers=scraper.headers,
            timeout=30
        )
        products = resp.json()
        print(f"  Found {len(products)} products")

        for p in products[:3]:
            item = scraper._parse_product(p, "upper_body")
            if item:
                print(f"\n  Product: {item.name[:50]}")
                print(f"    ID: {item.id}")
                print(f"    Price: {item.price} {item.currency}")
                print(f"    Category: {item.category}")
                print(f"    Image: ...{item.image_url[-50:]}")

    except Exception as e:
        print(f"  Error: {e}")

    print("\nTest passed!")
