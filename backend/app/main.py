from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.routers import tryon, recommend

app = FastAPI(title="AI Fashion Stylist API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files path
static_path = Path(__file__).parent / "data"


# Custom route for static files with CORS headers
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    file_full_path = static_path / file_path
    if file_full_path.exists() and file_full_path.is_file():
        response = FileResponse(file_full_path)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    raise HTTPException(status_code=404, detail="File not found")

app.include_router(tryon.router, prefix="/api", tags=["try-on"])
app.include_router(recommend.router, prefix="/api", tags=["recommendations"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
