from fashion_clip.fashion_clip import FashionCLIP
import numpy as np
from PIL import Image


class EmbeddingService:
    def __init__(self, model_name: str = "fashion-clip"):
        """Initialize FashionCLIP model for embeddings.

        Args:
            model_name: FashionCLIP model name (default: "fashion-clip")
        """
        self.fclip = FashionCLIP(model_name)

    def embed_image(self, image: Image.Image) -> np.ndarray:
        """Generate normalized embedding for a single image."""
        embedding = self.fclip.encode_images([image], batch_size=1)[0]
        embedding = embedding / np.linalg.norm(embedding, ord=2)

        if np.isnan(embedding).any():
            raise ValueError("Embedding contains NaN values")

        return embedding

    def embed_images(self, images: list[Image.Image], batch_size: int = 32) -> np.ndarray:
        """Generate normalized embeddings for multiple images."""
        embeddings = self.fclip.encode_images(images, batch_size=batch_size)
        embeddings = embeddings / np.linalg.norm(embeddings, ord=2, axis=-1, keepdims=True)
        return embeddings

    def embed_text(self, text: str) -> np.ndarray:
        """Generate normalized embedding for a single text."""
        embedding = self.fclip.encode_text([text], batch_size=1)[0]
        embedding = embedding / np.linalg.norm(embedding, ord=2)
        return embedding

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Generate normalized embeddings for multiple texts."""
        embeddings = self.fclip.encode_text(texts, batch_size=batch_size)
        embeddings = embeddings / np.linalg.norm(embeddings, ord=2, axis=-1, keepdims=True)
        return embeddings


if __name__ == "__main__":
    print("Testing EmbeddingService with native FashionCLIP...")
    print("Loading FashionCLIP model (this may take a moment)...")

    service = EmbeddingService()
    print("Model loaded!")

    # Create a simple test image (red square representing a garment)
    print("\nCreating test image...")
    img = Image.new("RGB", (224, 224), color=(200, 50, 50))
    print(f"  Image size: {img.size}")

    # Generate single image embedding
    print("\nGenerating single image embedding...")
    embedding = service.embed_image(img)
    print(f"  Embedding shape: {embedding.shape}")
    print(f"  Embedding dtype: {embedding.dtype}")
    print(f"  First 5 values: {embedding[:5]}")

    # Test batch image embedding
    print("\nGenerating batch image embeddings...")
    imgs = [img, Image.new("RGB", (224, 224), color=(50, 50, 200))]
    embeddings = service.embed_images(imgs, batch_size=2)
    print(f"  Batch embeddings shape: {embeddings.shape}")

    # Test text embedding
    print("\nGenerating text embedding for 'red shirt'...")
    text_embedding = service.embed_text("red shirt")
    print(f"  Text embedding shape: {text_embedding.shape}")

    # Test batch text embedding
    print("\nGenerating batch text embeddings...")
    text_embeddings = service.embed_texts(["red shirt", "blue pants"], batch_size=2)
    print(f"  Batch text embeddings shape: {text_embeddings.shape}")

    # Test similarity (embeddings are already normalized)
    similarity = np.dot(embedding, text_embedding)
    print(f"\n  Cosine similarity with 'red shirt': {similarity:.4f}")

    similarity2 = np.dot(embedding, text_embeddings[1])
    print(f"  Cosine similarity with 'blue pants': {similarity2:.4f}")

    print("\nTest passed!")
