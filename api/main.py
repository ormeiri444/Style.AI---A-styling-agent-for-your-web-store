from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from api.routes import tryon, recommend
except ImportError:
    from routes import tryon, recommend

app = FastAPI(
    title="Stylist AI",
    description="Virtual try-on + style recommendations powered by FastFit and FashionCLIP",
    version="1.0.0"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tryon.router, prefix="/api/tryon", tags=["Try-On"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["Recommendations"])


@app.get("/")
async def root():
    return {
        "name": "Stylist AI",
        "version": "1.0.0",
        "endpoints": {
            "try_on_single": "POST /api/tryon/single",
            "try_on_multi": "POST /api/tryon/multi",
            "get_complementary": "POST /api/recommend/complementary",
            "get_catalog": "GET /api/recommend/catalog"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    print("Testing API main...")
    print(f"\nApp title: {app.title}")
    print(f"App version: {app.version}")

    print("\nRegistered routes:")
    for route in app.routes:
        methods = getattr(route, 'methods', {'*'})
        path = getattr(route, 'path', str(route))
        print(f"  {methods} {path}")

    print("\nTo start the server, run:")
    print("  uvicorn api.main:app --reload")
    print("\nTest passed!")
