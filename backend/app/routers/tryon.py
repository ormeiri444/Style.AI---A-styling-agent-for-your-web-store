import traceback
from fastapi import APIRouter, HTTPException

from app.models.schemas import TryOnRequest, TryOnResponse, AddItemRequest
from app.services.gemini_tryon import perform_tryon, add_item_to_outfit

router = APIRouter()


@router.post("/tryon", response_model=TryOnResponse)
async def tryon(request: TryOnRequest):
    try:
        print(f"[tryon] Received request - human_image length: {len(request.human_image)}, garment_image length: {len(request.garment_image)}")
        print(f"[tryon] Category: {request.category}, Description: {request.garment_description[:50]}...")
        result_image = await perform_tryon(
            human_image_b64=request.human_image,
            garment_image_b64=request.garment_image,
            garment_description=request.garment_description,
            category=request.category,
        )
        print(f"[tryon] Success - result_image length: {len(result_image)}")
        return TryOnResponse(
            result_image=result_image,
            outfit_state={"worn_items": [{"category": request.category, "description": request.garment_description}]},
        )
    except Exception as e:
        print(f"[tryon] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tryon/add-item", response_model=TryOnResponse)
async def add_item(request: AddItemRequest):
    try:
        result_image = await add_item_to_outfit(
            current_outfit_image_b64=request.current_outfit_image,
            new_item_image_b64=request.new_item_image,
            item_description=request.item_description,
        )
        return TryOnResponse(
            result_image=result_image,
            outfit_state={"worn_items": []},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
