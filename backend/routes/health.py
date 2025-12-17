from fastapi import APIRouter


router = APIRouter(
    prefix="",
    tags=["health"],
)


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Semantic Join API",
        "version": "0.2.0",
        "endpoints": {
            "/health": "GET - Health check endpoint",
            "/bridge-table": "POST - Create bridge table (supports RS-JP and CS-JP)",
            "/join-from-bridge": "POST - Perform three-way join (R ⋈ bridge ⋈ S)",
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
