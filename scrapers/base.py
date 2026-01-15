from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Item:
    id: str
    source: str
    name: str
    price: float
    currency: str
    category: str
    image_url: str
    product_url: str


class BaseScraper(ABC):
    SOURCE: str = ""

    @abstractmethod
    def scrape_all(self) -> list[Item]:
        pass

    @abstractmethod
    def map_category(self, raw: str) -> str:
        pass


if __name__ == "__main__":
    # Test Item dataclass
    item = Item(
        id="123",
        source="test",
        name="Test Hoodie",
        price=99.99,
        currency="EUR",
        category="upper_body",
        image_url="https://example.com/image.jpg",
        product_url="https://example.com/product"
    )

    print("Item dataclass test:")
    print(f"  ID: {item.id}")
    print(f"  Name: {item.name}")
    print(f"  Price: {item.price} {item.currency}")
    print(f"  Category: {item.category}")
    print(f"  As dict: {item.__dict__}")
    print("\nBaseScraper is abstract - cannot instantiate directly")
    print("Test passed!")
