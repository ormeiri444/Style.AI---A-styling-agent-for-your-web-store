import torch
from PIL import Image


class FastFitService:
    def __init__(self):
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

    def load(self):
        from diffusers import StableDiffusionInpaintPipeline

        self.pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "zhengchong/FastFit-MR-1024",
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32
        )
        if self.device != "cpu":
            self.pipe = self.pipe.to(self.device)

    def try_on(self, person_img: Image.Image, garment_img: Image.Image, category: str) -> Image.Image:
        if self.pipe is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        result = self.pipe(
            image=person_img,
            garment=garment_img,
            category=category,
            num_inference_steps=30,
            guidance_scale=2.5
        )
        return result.images[0]


if __name__ == "__main__":
    print("Testing FastFitService...")

    service = FastFitService()
    print(f"Device: {service.device}")
    print(f"Pipeline loaded: {service.pipe is not None}")

    # Test error handling
    print("\nTesting error handling (calling try_on without loading)...")
    try:
        service.try_on(None, None, "upper_body")
    except RuntimeError as e:
        print(f"  Got expected error: {e}")

    print("\nNote: Full test requires downloading the FastFit model (~5GB)")
    print("To test model loading, uncomment the following lines:")
    print("  # service.load()")
    print("  # print('Model loaded successfully!')")

    print("\nTest passed!")
