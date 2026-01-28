import json
from pathlib import Path
from typing import Optional

CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog.json"


def get_catalog(category: Optional[str] = None) -> list[dict]:
    if not CATALOG_PATH.exists():
        return []

    with open(CATALOG_PATH) as f:
        data = json.load(f)

    items = data.get("items", [])

    if category:
        items = [item for item in items if item.get("category") == category]

    return items
