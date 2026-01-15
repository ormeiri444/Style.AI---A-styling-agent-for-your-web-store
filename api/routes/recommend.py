from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Lazy load services
_vector_store = None
_embedding_service = None


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        from api.services.vector_store import VectorStore
        _vector_store = VectorStore()
    return _vector_store


def get_embedding_service():
    global _embedding_service
    if _embedding_service is None:
        from api.services.embeddings import EmbeddingService
        _embedding_service = EmbeddingService()
    return _embedding_service


class RecommendRequest(BaseModel):
    item_id: str
    categories: list[str]
    exclude_ids: list[str] = []


class Item(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    category: str
    image_url: str
    product_url: str


class RecommendResponse(BaseModel):
    items: list[Item]


@router.post("/complementary", response_model=RecommendResponse)
async def get_complementary(req: RecommendRequest):
    """Get complementary items based on a selected item."""
    try:
        store = get_vector_store()

        # Get the selected item's vector
        point = store.get_by_id(req.item_id)
        if point is None:
            raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")

        # Search for similar items in target categories
        results = store.search(
            vector=point.vector,
            categories=req.categories,
            exclude_ids=[req.item_id] + req.exclude_ids,
            limit=10
        )

        items = []
        for r in results:
            payload = r.payload
            items.append(Item(
                id=payload.get("id", ""),
                name=payload.get("name", ""),
                price=payload.get("price", 0.0),
                currency=payload.get("currency", "EUR"),
                category=payload.get("category", ""),
                image_url=payload.get("image_url", ""),
                product_url=payload.get("product_url", "")
            ))

        return RecommendResponse(items=items)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog")
async def get_catalog(category: str = None, limit: int = 50):
    """Get items from the catalog, optionally filtered by category."""
    try:
        store = get_vector_store()

        # Use a random vector to get items (we're not really searching by similarity here)
        import numpy as np
        random_vector = np.random.randn(512).astype(np.float32).tolist()

        categories = [category] if category else None
        results = store.search(
            vector=random_vector,
            categories=categories,
            limit=limit
        )

        items = []
        for r in results:
            payload = r.payload
            items.append({
                "id": payload.get("id", ""),
                "name": payload.get("name", ""),
                "price": payload.get("price", 0.0),
                "currency": payload.get("currency", "EUR"),
                "category": payload.get("category", ""),
                "image_url": payload.get("image_url", ""),
                "product_url": payload.get("product_url", "")
            })

        return {"items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Testing recommend routes...")

    # Test route definitions
    print(f"\nRoutes defined:")
    for route in router.routes:
        methods = getattr(route, 'methods', {'GET'})
        print(f"  {methods} {route.path} -> {route.name}")

    # Test models
    print("\nTesting Pydantic models:")
    req = RecommendRequest(
        item_id="123",
        categories=["lower_body", "shoes"],
        exclude_ids=["456"]
    )
    print(f"  RecommendRequest: {req.model_dump()}")

    item = Item(
        id="789",
        name="Blue Jeans",
        price=79.99,
        currency="EUR",
        category="lower_body",
        image_url="https://example.com/jeans.jpg",
        product_url="https://example.com/product/jeans"
    )
    print(f"  Item: {item.model_dump()}")

    print("\nNote: Full testing requires Qdrant running")
    print("Start Qdrant with: docker run -p 6333:6333 qdrant/qdrant")
    print("\nTest passed!")
