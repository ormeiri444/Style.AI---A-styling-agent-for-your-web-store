"""Scrape product images and metadata from terminalx.com"""
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time

BASE_URL = "https://www.terminalx.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

CATEGORIES = [
    ("/women/tops", "upper_body", "women"),
    ("/women/jeans", "lower_body", "women"),
    ("/women/shoes", "shoes", "women"),
    ("/men/shirts", "upper_body", "men"),
    ("/men/pants", "lower_body", "men"),
    ("/men/shoes", "shoes", "men"),
]

OUTPUT_DIR = Path(__file__).parent.parent / "backend" / "app" / "data"
IMAGES_DIR = OUTPUT_DIR / "catalog_images"


def extract_products_from_page(html: str, category: str, gender: str, limit: int = 2) -> list:
    """Extract product data from page HTML by finding embedded JSON."""
    products = []
    soup = BeautifulSoup(html, "html.parser")

    # Look for product images in img tags
    img_tags = soup.find_all("img")
    seen_images = set()

    for img in img_tags:
        src = img.get("src", "") or img.get("data-src", "")
        alt = img.get("alt", "")

        # Filter for product images from their CDN
        if "media.terminalx.com" in src and "catalog/product" in src:
            if src in seen_images:
                continue
            seen_images.add(src)

            # Clean up the name - extract brand and product info
            name = alt.strip() if alt else "Unknown Product"

            products.append({
                "name": name,
                "image": src,
                "category": category,
                "gender": gender,
            })

            if len(products) >= limit:
                break

    return products[:limit]


def fetch_category_page(url_path: str) -> str:
    """Fetch a category page."""
    url = BASE_URL + url_path
    print(f"Fetching: {url}")
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def download_image(url: str, filename: str) -> bool:
    """Download an image to the catalog_images folder."""
    try:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        filepath = IMAGES_DIR / filename
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"  Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"  Failed to download {url}: {e}")
        return False


def extract_color_from_name(name: str) -> str:
    """Try to extract color from product name."""
    colors = ["black", "white", "blue", "red", "green", "navy", "grey", "gray",
              "brown", "beige", "pink", "purple", "orange", "yellow", "cream",
              "שחור", "לבן", "כחול", "אדום", "ירוק", "אפור", "חום", "בז'"]
    name_lower = name.lower()
    for color in colors:
        if color in name_lower:
            return color
    return "multi"


def extract_brand_from_name(name: str) -> str:
    """Extract brand from product name (usually after 'של' in Hebrew)."""
    if " של " in name:
        return name.split(" של ")[-1].strip()
    # Try to find known brands
    brands = ["ADIDAS", "NIKE", "CONVERSE", "BROOKS", "ASICS", "MANGO", "ZARA",
              "BROWNIE", "LEVIS", "LEVI'S", "TOMMY", "PUMA", "REEBOK", "NEW BALANCE"]
    for brand in brands:
        if brand.lower() in name.lower():
            return brand
    return "Unknown"


def main():
    all_products = []
    product_id = 1

    for url_path, category, gender in CATEGORIES:
        print(f"\n--- Scraping {gender} {category} ---")
        try:
            html = fetch_category_page(url_path)
            products = extract_products_from_page(html, category, gender, limit=2)

            for p in products:
                p["id"] = f"{category}_{product_id:03d}"
                p["brand"] = extract_brand_from_name(p["name"])
                p["color"] = extract_color_from_name(p["name"])
                product_id += 1

            all_products.extend(products)
            print(f"  Found {len(products)} products")
            time.sleep(1)
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n=== Total products found: {len(all_products)} ===")

    # Download images and build catalog
    catalog_items = []

    for p in all_products:
        # Determine file extension from URL
        img_url = p["image"]
        ext = "jpg"
        if ".png" in img_url:
            ext = "png"
        elif ".webp" in img_url:
            ext = "webp"

        filename = f"{p['id']}.{ext}"

        print(f"\nProcessing: {p['name'][:50]}...")
        if download_image(img_url, filename):
            # Determine style based on category and brand
            styles = ["casual"]
            if p["brand"].upper() in ["ADIDAS", "NIKE", "PUMA", "BROOKS", "ASICS"]:
                styles.append("sporty")
            if "jeans" in p["name"].lower() or "ג'ינס" in p["name"]:
                styles.append("streetwear")

            catalog_items.append({
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "subcategory": p["category"],  # Could be refined
                "color": p["color"],
                "style": styles,
                "image_path": f"catalog_images/{filename}",
                "description": p["name"],
                "gender": p["gender"],
                "brand": p["brand"],
                "source_url": img_url,
            })

    # Save catalog
    catalog = {"items": catalog_items}
    catalog_path = OUTPUT_DIR / "catalog.json"

    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"\n=== Saved {len(catalog_items)} items to catalog.json ===")
    return catalog_items


if __name__ == "__main__":
    products = main()
