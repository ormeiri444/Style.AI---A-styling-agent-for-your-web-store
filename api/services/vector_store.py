from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchAny


class VectorStore:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection = "fashion_items"

    def create_collection(self, recreate=False):
        if recreate:
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)
        )

    def collection_exists(self):
        collections = self.client.get_collections().collections
        return any(c.name == self.collection for c in collections)

    def upsert(self, item_id, vector, payload):
        # Qdrant requires integer or UUID for point IDs
        # Convert string IDs to integers
        numeric_id = int(item_id) if isinstance(item_id, str) and item_id.isdigit() else hash(item_id) % (2**63)
        self.client.upsert(self.collection, [
            PointStruct(id=numeric_id, vector=vector, payload=payload)
        ])

    def search(self, vector, categories=None, exclude_ids=None, limit=10):
        query_filter = None

        if categories or exclude_ids:
            must = []
            must_not = []

            if categories:
                must.append(FieldCondition(
                    key="category",
                    match=MatchAny(any=categories)
                ))

            if exclude_ids:
                must_not.append(FieldCondition(
                    key="id",
                    match=MatchAny(any=exclude_ids)
                ))

            query_filter = Filter(must=must if must else None, must_not=must_not if must_not else None)

        return self.client.search(
            self.collection,
            query_vector=vector,
            query_filter=query_filter,
            limit=limit
        )

    def get_by_id(self, item_id):
        # Convert string ID to numeric ID
        numeric_id = int(item_id) if isinstance(item_id, str) and item_id.isdigit() else hash(item_id) % (2**63)
        results = self.client.retrieve(self.collection, ids=[numeric_id])
        return results[0] if results else None


if __name__ == "__main__":
    import numpy as np

    print("Testing VectorStore...")
    print("Note: This test requires Qdrant running on localhost:6333")
    print("You can start it with: docker run -p 6333:6333 qdrant/qdrant\n")

    try:
        store = VectorStore()

        # Test connection
        print("Checking connection to Qdrant...")
        collections = store.client.get_collections()
        print(f"  Connected! Found {len(collections.collections)} collections")

        # Create test collection
        print("\nCreating test collection...")
        if store.collection_exists():
            print("  Collection exists, recreating...")
            store.create_collection(recreate=True)
        else:
            store.create_collection()
        print("  Collection created!")

        # Insert test items
        print("\nInserting test items...")
        test_items = [
            {"id": "1", "name": "Black Hoodie", "category": "upper_body", "price": 99.0},
            {"id": "2", "name": "Blue Jeans", "category": "lower_body", "price": 79.0},
            {"id": "3", "name": "White Sneakers", "category": "shoes", "price": 129.0},
        ]

        for item in test_items:
            # Create random vector for testing
            vector = np.random.randn(512).astype(np.float32).tolist()
            store.upsert(item["id"], vector, item)
            print(f"  Inserted: {item['name']}")

        # Test search
        print("\nSearching for similar items...")
        query_vector = np.random.randn(512).astype(np.float32).tolist()
        results = store.search(query_vector, limit=3)
        print(f"  Found {len(results)} results:")
        for r in results:
            print(f"    - {r.payload['name']} (score: {r.score:.4f})")

        # Test filtered search
        print("\nSearching with category filter (upper_body)...")
        results = store.search(query_vector, categories=["upper_body"], limit=3)
        print(f"  Found {len(results)} results:")
        for r in results:
            print(f"    - {r.payload['name']} ({r.payload['category']})")

        print("\nTest passed!")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure Qdrant is running:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
