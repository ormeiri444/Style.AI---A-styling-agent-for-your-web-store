import base64
import io
import json

from google import genai
from google.genai import types
from PIL import Image

from app.config import GOOGLE_API_KEY


def _get_client():
    return genai.Client(api_key=GOOGLE_API_KEY)


def _b64_to_image(b64_string: str) -> Image.Image:
    image_data = base64.b64decode(b64_string)
    return Image.open(io.BytesIO(image_data))


async def get_recommendations(
    outfit_image_b64: str,
    worn_items: list[dict],
    catalog: list[dict],
) -> list[dict]:
    client = _get_client()

    outfit_img = _b64_to_image(outfit_image_b64)

    catalog_text = "\n".join(
        [
            f"- ID: {item['id']}, Name: {item['name']}, Category: {item['category']}, "
            f"Color: {item['color']}, Style: {', '.join(item['style'])}"
            for item in catalog
        ]
    )

    prompt = f"""
    Analyze this outfit image and recommend complementary clothing items.

    Currently wearing:
    {json.dumps(worn_items, indent=2)}

    Available items in catalog:
    {catalog_text}

    Based on:
    1. Color harmony and coordination
    2. Style consistency
    3. Occasion appropriateness
    4. Fashion principles

    Recommend 3-5 items that would complete or enhance this look.

    Return ONLY valid JSON in this exact format:
    {{
        "recommendations": [
            {{
                "id": "item_id",
                "reason": "Brief explanation of why this item complements the outfit"
            }}
        ],
        "style_analysis": "Brief description of the current outfit's style"
    }}
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[outfit_img, prompt],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT"],
        ),
    )

    response_text = response.text
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    result = json.loads(response_text.strip())

    enriched = []
    for rec in result["recommendations"]:
        item = next((i for i in catalog if i["id"] == rec["id"]), None)
        if item:
            enriched.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "image_url": item["image_path"],
                    "category": item["category"],
                    "reason": rec["reason"],
                }
            )

    return enriched
