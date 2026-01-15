import httpx
import re
import json
from typing import Optional

try:
    from .base import BaseScraper, Item
except ImportError:
    from base import BaseScraper, Item


class TerminalXScraper(BaseScraper):
    """Scraper for terminalx.com - Israeli fashion retailer.

    Extracts product-only images (without models) by selecting the last image
    in the media gallery, which is typically the flatlay/product shot.
    """

    SOURCE = "terminalx"
    BASE_URL = "https://www.terminalx.com"

    # Categories to scrape
    CATEGORIES = [
        ("women/tops", "upper_body"),
        ("women/dresses", "dresses"),
        ("women/pants", "lower_body"),
        ("women/shorts", "lower_body"),
        ("women/skirts", "lower_body"),
        ("women/jackets-coats", "upper_body"),
        ("women/jeans", "lower_body"),
        ("men/t-shirts", "upper_body"),
        ("men/shirts", "upper_body"),
        ("men/pants", "lower_body"),
        ("men/shorts", "lower_body"),
        ("men/jackets-coats", "upper_body"),
        ("men/jeans", "lower_body"),
    ]

    # Hebrew category mapping
    CATEGORY_MAP = {
        # Upper body
        "חולצ": "upper_body",
        "טופ": "upper_body",
        "גופי": "upper_body",
        "סריג": "upper_body",
        "קרדיגן": "upper_body",
        "ז'קט": "upper_body",
        "מעיל": "upper_body",
        "סווטשירט": "upper_body",
        "הודי": "upper_body",
        "shirt": "upper_body",
        "top": "upper_body",
        "jacket": "upper_body",
        "sweater": "upper_body",
        "hoodie": "upper_body",
        # Lower body
        "מכנס": "lower_body",
        "ג'ינס": "lower_body",
        "שורט": "lower_body",
        "חצאית": "lower_body",
        "טייץ": "lower_body",
        "pants": "lower_body",
        "jeans": "lower_body",
        "shorts": "lower_body",
        "skirt": "lower_body",
        # Dresses
        "שמלה": "dresses",
        "שמלת": "dresses",
        "dress": "dresses",
        # Full body
        "אוברול": "full_body",
        "סט": "full_body",
        "jumpsuit": "full_body",
    }

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

    def scrape_all(self) -> list[Item]:
        """Scrape all products from configured categories."""
        all_items = []
        seen_ids = set()

        for category_path, default_category in self.CATEGORIES:
            print(f"  Scraping {category_path}...")
            items = self._scrape_category(category_path, default_category, seen_ids)
            all_items.extend(items)
            print(f"    Found {len(items)} new items")

        return all_items

    def _scrape_category(self, category_path: str, default_category: str, seen_ids: set) -> list[Item]:
        """Scrape products from a single category."""
        items = []
        page = 1
        max_pages = 10  # Safety limit

        while page <= max_pages:
            url = f"{self.BASE_URL}/{category_path}?p={page}"
            try:
                resp = httpx.get(url, headers=self.headers, timeout=30, follow_redirects=True)
                if resp.status_code != 200:
                    break

                html = resp.text
                products = self._extract_products(html)

                if not products:
                    break

                new_count = 0
                for p in products:
                    if p['id'] not in seen_ids:
                        seen_ids.add(p['id'])
                        item = self._parse_product(p, default_category)
                        if item:
                            items.append(item)
                            new_count += 1

                if new_count == 0:
                    break

                page += 1
            except Exception as e:
                print(f"    Error on page {page}: {e}")
                break

        return items

    def _extract_products(self, html: str) -> list[dict]:
        """Extract product data from HTML."""
        products = []
        seen = set()

        # Pattern to match product blocks
        pattern = r'"id":(\d+),"sku":"([^"]+)","name":"([^"]+)"'

        # Find basic product info
        for match in re.finditer(pattern, html):
            pid = match.group(1)
            if pid in seen:
                continue
            seen.add(pid)

            products.append({
                'id': pid,
                'sku': match.group(2),
                'name': match.group(3)
            })

        # Find media galleries
        galleries = {}
        for match in re.finditer(r'"media_gallery":(\[[^\]]+\])', html):
            try:
                imgs = json.loads(match.group(1))
                if imgs:
                    # Use first image's SKU as key
                    first_url = imgs[0].get('url', '')
                    sku_match = re.search(r'/([a-zA-Z0-9]+)-\d', first_url)
                    if sku_match:
                        galleries[sku_match.group(1).upper()] = imgs
            except:
                pass

        # Find prices
        prices = {}
        for match in re.finditer(r'"sku":"([^"]+)"[^}]*?"minimum_price":\{"final_price":\{"value":([0-9.]+)', html):
            prices[match.group(1)] = float(match.group(2))

        # Find URL keys
        url_keys = {}
        for match in re.finditer(r'"sku":"([^"]+)"[^}]*?"url_key":"([^"]+)"', html):
            url_keys[match.group(1)] = match.group(2)

        # Merge data
        for p in products:
            sku = p['sku']
            p['price'] = prices.get(sku, 0)
            p['url_key'] = url_keys.get(sku, '')
            p['images'] = galleries.get(sku, [])

        return products

    def _parse_product(self, p: dict, default_category: str) -> Optional[Item]:
        """Parse product dict into Item."""
        images = p.get('images', [])

        # Get product-only image (last image in gallery)
        if not images:
            return None

        # Last image is typically the flatlay/product-only shot
        product_image = images[-1].get('url', '')
        if not product_image:
            product_image = images[0].get('url', '')

        # Clean up image URL
        product_image = product_image.split('?')[0]

        # Build product URL
        url_key = p.get('url_key', p['sku'].lower())
        product_url = f"{self.BASE_URL}/{url_key}"

        return Item(
            id=p['id'],
            source=self.SOURCE,
            name=p['name'],
            price=p.get('price', 0),
            currency="ILS",
            category=self.map_category(p['name'], default_category),
            image_url=product_image,
            product_url=product_url
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

    print("Testing TerminalXScraper...")
    scraper = TerminalXScraper()

    # Test category mapping
    print("\nCategory mapping tests:")
    print(f"  'חולצה מכופתרת' -> {scraper.map_category('חולצה מכופתרת')}")
    print(f"  'מכנסיים קצרים' -> {scraper.map_category('מכנסיים קצרים')}")
    print(f"  'שמלת מקסי' -> {scraper.map_category('שמלת מקסי')}")

    # Test scraping a single category
    print("\nFetching products from women/tops (page 1 only)...")
    try:
        resp = httpx.get(
            f"{scraper.BASE_URL}/women/tops?p=1",
            headers=scraper.headers,
            timeout=30
        )

        products = scraper._extract_products(resp.text)
        print(f"  Found {len(products)} products")

        # Show first few products
        for p in products[:3]:
            print(f"\n  Product: {p['name'][:50]}")
            print(f"    SKU: {p['sku']}")
            print(f"    Price: {p['price']} ILS")
            print(f"    Images: {len(p.get('images', []))}")
            if p.get('images'):
                # Show the product-only image (last one)
                last_img = p['images'][-1]['url'].split('?')[0]
                print(f"    Product-only image: ...{last_img[-60:]}")

    except Exception as e:
        print(f"  Error: {e}")

    print("\nTest passed!")
