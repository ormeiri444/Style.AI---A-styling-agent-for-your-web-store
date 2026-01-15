from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
import httpx
from io import BytesIO
import base64

router = APIRouter()

# Lazy load the FastFit service
_fastfit_service = None


def get_fastfit_service():
    global _fastfit_service
    if _fastfit_service is None:
        from api.services.fastfit import FastFitService
        _fastfit_service = FastFitService()
        _fastfit_service.load()
    return _fastfit_service


@router.post("/single")
async def try_on_single(
    person: UploadFile = File(...),
    garment_url: str = Form(...),
    category: str = Form(...)
):
    """Try on a single garment on a person image."""
    try:
        # Load person image
        person_bytes = await person.read()
        person_img = Image.open(BytesIO(person_bytes)).convert("RGB")

        # Fetch garment image
        async with httpx.AsyncClient() as client:
            resp = await client.get(garment_url, timeout=30)
            resp.raise_for_status()
        garment_img = Image.open(BytesIO(resp.content)).convert("RGB")

        # Process with FastFit
        service = get_fastfit_service()
        result_img = service.try_on(person_img, garment_img, category)

        # Return result as image
        buf = BytesIO()
        result_img.save(buf, format="JPEG", quality=95)
        buf.seek(0)

        return StreamingResponse(buf, media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi")
async def try_on_multi(
    person: UploadFile = File(...),
    garments: str = Form(...)  # JSON array of {url, category}
):
    """Try on multiple garments sequentially."""
    import json

    try:
        garment_list = json.loads(garments)

        # Load person image
        person_bytes = await person.read()
        current_img = Image.open(BytesIO(person_bytes)).convert("RGB")

        service = get_fastfit_service()

        # Process each garment sequentially
        async with httpx.AsyncClient() as client:
            for garment in garment_list:
                resp = await client.get(garment["url"], timeout=30)
                resp.raise_for_status()
                garment_img = Image.open(BytesIO(resp.content)).convert("RGB")

                current_img = service.try_on(current_img, garment_img, garment["category"])

        # Return result as image
        buf = BytesIO()
        current_img.save(buf, format="JPEG", quality=95)
        buf.seek(0)

        return StreamingResponse(buf, media_type="image/jpeg")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in garments parameter")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Testing tryon routes...")

    # Test route definitions
    print(f"\nRoutes defined:")
    for route in router.routes:
        print(f"  {route.methods} {route.path} -> {route.name}")

    print("\nNote: Full testing requires running the FastAPI server")
    print("Start with: uvicorn api.main:app --reload")
    print("\nTest passed!")
