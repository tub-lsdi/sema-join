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
        "version": "0.3.0",
        "endpoints": {
            "/health": "GET - Health check endpoint",
            "/bridge-table": "POST - Create bridge table (supports RS-JP and CS-JP-LP)",
            "/join-from-bridge": "POST - Perform three-way join (R ⋈ bridge ⋈ S)",
            "/history": "GET - Get list of join history",
            "/history/{id}": "GET - Get detailed history entry with tables",
            "/tables/upload": "POST - Upload a CSV table",
            "/tables": "GET - List all uploaded tables",
            "/tables/{id}": "GET - Get table details, DELETE - Delete table",
            "/ai/recommend-columns": "POST - Get AI column join recommendations",
            "/ai/recommend-bridge-entries": "POST - Get AI bridge entry recommendations",
            "/ai/status": "GET - Check Ollama AI service status",
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
