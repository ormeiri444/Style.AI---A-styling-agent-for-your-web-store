#!/usr/bin/env python
"""Generate embeddings for catalog items and store in Qdrant."""

import sys
import json
from pathlib import Path
from io import BytesIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from PIL import Image

from api.services.embeddings import EmbeddingService
from api.services.vector_store import VectorStore


def load_catalog(catalog_dir: Path, source: str = None) -> list[dict]:
    """Load catalog items from JSON files."""
    items = []

    if source:
        files = [catalog_dir / f"{source}.json"]
    else:
        files = list(catalog_dir.glob("*.json"))

    for f in files:
        if f.exists() and not f.name.endswith("_test.json"):
            with open(f) as fp:
                items.extend(json.load(fp))

    return items


def embed_items(items: list[dict], emb_service: EmbeddingService, store: VectorStore, skip_errors: bool = True):
    """Generate embeddings and store in Qdrant."""
    success = 0
    errors = 0

    for i, item in enumerate(items):
        try:
            # Fetch image
            resp = httpx.get(item["image_url"], timeout=30)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content)).convert("RGB")

            # Generate embedding
            vector = emb_service.embed_image(img)

            # Store in Qdrant
            store.upsert(item["id"], vector.tolist(), item)

            success += 1
            print(f"  [{i+1}/{len(items)}] {item['name']}")

        except Exception as e:
            errors += 1
            if skip_errors:
                print(f"  [{i+1}/{len(items)}] ERROR: {item['name']} - {e}")
            else:
                raise

    return success, errors


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate embeddings for catalog items")
    parser.add_argument(
        "--source", "-s",
        help="Specific source to embed (default: all)"
    )
    parser.add_argument(
        "--catalog", "-c",
        default="data/catalog",
        help="Catalog directory (default: data/catalog)"
    )
    parser.add_argument(
        "--recreate", "-r",
        action="store_true",
        help="Recreate the collection (delete existing data)"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run in test mode (process test catalog file)"
    )
    args = parser.parse_args()

    catalog_dir = Path(args.catalog)

    if args.test:
        print("Running in test mode...")

        # Load test catalog
        test_file = catalog_dir / "matimli_test.json"
        if not test_file.exists():
            print(f"Test file not found: {test_file}")
            print("Run 'python scripts/scrape.py --test' first")
            sys.exit(1)

        with open(test_file) as f:
            items = json.load(f)

        print(f"Loaded {len(items)} test items")

        # Initialize services
        print("\nLoading FashionCLIP model...")
        emb_service = EmbeddingService()
        print("Model loaded!")

        # Test embedding without Qdrant
        print("\nGenerating embeddings (no Qdrant)...")
        for i, item in enumerate(items[:2]):  # Only test 2 items
            try:
                resp = httpx.get(item["image_url"], timeout=30)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")

                vector = emb_service.embed_image(img)
                print(f"  [{i+1}] {item['name']}")
                print(f"      Vector shape: {vector.shape}")
                print(f"      First 5 values: {vector[:5]}")
            except Exception as e:
                print(f"  [{i+1}] ERROR: {item['name']} - {e}")

        print("\nTest completed!")
        print("To fully test with Qdrant, start it with:")
        print("  docker run -p 6333:6333 qdrant/qdrant")

    else:
        # Load catalog
        items = load_catalog(catalog_dir, args.source)
        if not items:
            print("No catalog items found. Run 'python scripts/scrape.py' first.")
            sys.exit(1)

        print(f"Loaded {len(items)} items from catalog")

        # Initialize services
        print("\nLoading FashionCLIP model...")
        emb_service = EmbeddingService()
        print("Model loaded!")

        print("\nConnecting to Qdrant...")
        store = VectorStore()

        # Create/recreate collection
        if args.recreate or not store.collection_exists():
            print("Creating collection...")
            store.create_collection(recreate=args.recreate)
        print("Connected!")

        # Generate embeddings
        print(f"\nGenerating embeddings for {len(items)} items...")
        success, errors = embed_items(items, emb_service, store)

        print(f"\nCompleted!")
        print(f"  Success: {success}")
        print(f"  Errors: {errors}")
