import base64
import io

from google import genai
from google.genai import types
from PIL import Image
import pillow_heif

# Register HEIF/HEIC support with Pillow
pillow_heif.register_heif_opener()

from pathlib import Path

from app.config import GOOGLE_API_KEY, IMAGE_OUTPUT_SIZE

# Load prompt templates
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    return prompt_path.read_text()


def _get_client():
    return genai.Client(api_key=GOOGLE_API_KEY)


def _b64_to_image(b64_string: str) -> Image.Image:
    # Handle potential data URL prefix
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]

    # Clean up the base64 string (remove whitespace, handle URL-safe encoding)
    b64_string = b64_string.strip()
    b64_string = b64_string.replace('-', '+').replace('_', '/')

    # Add padding if needed
    padding = 4 - len(b64_string) % 4
    if padding != 4:
        b64_string += '=' * padding

    print(f"[_b64_to_image] Base64 string first 100 chars: {b64_string[:100]}")

    try:
        image_data = base64.b64decode(b64_string)
        print(f"[_b64_to_image] Decoded {len(image_data)} bytes")
        return Image.open(io.BytesIO(image_data))
    except Exception as e:
        print(f"[_b64_to_image] Decode error: {e}")
        raise


def _image_to_b64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


async def perform_tryon(
    human_image_b64: str,
    garment_image_b64: str,
    garment_description: str,
    category: str = "upper_body",
) -> str:
    print(f"[gemini_tryon] Starting perform_tryon...")
    client = _get_client()
    print(f"[gemini_tryon] Client created")

    human_img = _b64_to_image(human_image_b64)
    print(f"[gemini_tryon] Human image decoded: {human_img.size}")
    garment_img = _b64_to_image(garment_image_b64)
    print(f"[gemini_tryon] Garment image decoded: {garment_img.size}")

    # Load and format the prompt template
    prompt_template = _load_prompt("tryon_prompt.md")
    prompt = prompt_template.format(
        category=category,
        garment_description=garment_description
    )

    print(f"[gemini_tryon] Calling Gemini API...")
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=[prompt, human_img, garment_img],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    print(f"[gemini_tryon] Response received, candidates: {len(response.candidates) if response.candidates else 0}")

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            print(f"[gemini_tryon] Found inline_data in response")
            image_data = part.inline_data.data
            result_image = Image.open(io.BytesIO(image_data))
            return _image_to_b64(result_image)

    print(f"[gemini_tryon] No image found in response parts")
    raise Exception("No image generated")


async def add_item_to_outfit(
    current_outfit_image_b64: str,
    new_item_image_b64: str,
    item_description: str,
    worn_items: list[str] | None = None,
) -> str:
    client = _get_client()

    current_img = _b64_to_image(current_outfit_image_b64)
    new_item_img = _b64_to_image(new_item_image_b64)

    worn_items = worn_items or []
    worn_items_str = ", ".join(worn_items) if worn_items else "the current outfit"

    # Load and format the prompt template
    prompt_template = _load_prompt("add_item_prompt.md")
    prompt = prompt_template.format(
        worn_items_str=worn_items_str,
        item_description=item_description
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=[prompt, current_img, new_item_img],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data
            result_image = Image.open(io.BytesIO(image_data))
            return _image_to_b64(result_image)

    raise Exception("No image generated")
