from pydantic import BaseModel
from typing import Optional


class TryOnRequest(BaseModel):
    human_image: str  # base64 encoded
    garment_image: str  # base64 encoded
    garment_description: str
    category: str = "upper_body"


class TryOnResponse(BaseModel):
    result_image: str  # base64 encoded
    outfit_state: dict


class AddItemRequest(BaseModel):
    current_outfit_image: str  # base64 encoded
    new_item_image: str  # base64 encoded
    item_description: str


class RecommendRequest(BaseModel):
    current_outfit_image: str  # base64 encoded
    worn_items: list[dict]
    preferences: Optional[dict] = None


class RecommendationItem(BaseModel):
    id: str
    name: str
    image_url: str
    category: str
    reason: str


class RecommendResponse(BaseModel):
    recommendations: list[RecommendationItem]


class CatalogItem(BaseModel):
    id: str
    name: str
    category: str
    subcategory: str
    color: str
    style: list[str]
    image_path: str
    description: str
