"""
Health check and API information endpoints.
"""
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
        "workflow": [
            "1. POST /bridge-table → Get best matches using selected algorithm",
            "   • join_method='row': RS-JP",
            "   • join_method='column': CS-JP",
            "2. POST /join-from-bridge → Three-way join: list_r ⋈ bridge_table ⋈ list_s"
        ],
        "algorithms": {
            "RS-JP (row)": "Fast greedy algorithm using row-level co-occurrence",
            "CS-JP (column)": "Global optimization considering semantic compatibility between matched pairs"
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

