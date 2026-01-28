from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.schemas import RecommendRequest, RecommendResponse
from app.services.gemini_recommend import get_recommendations
from app.services.catalog_service import get_catalog

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    try:
        catalog = get_catalog()
        recommendations = await get_recommendations(
            outfit_image_b64=request.current_outfit_image,
            worn_items=request.worn_items,
            catalog=catalog,
        )
        return RecommendResponse(recommendations=recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog")
async def catalog(category: Optional[str] = Query(None)):
    items = get_catalog(category=category)
    return {"items": items}
