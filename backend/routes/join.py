"""
Join endpoint routes.
"""
from fastapi import APIRouter, HTTPException, Request

from backend.models import (
    JoinResponse,
    BridgeTableRequest,
    BridgeTableResponse,
    JoinWithBridgeRequest,
)
from backend.services import SemanticJoinService


router = APIRouter(
    prefix="",
    tags=["join"],
)


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Semantic Join API",
        "version": "0.1.0",
        "endpoints": {
            "/health": "GET - Health check endpoint",
            "/bridge-table": "POST - Create bridge table with all candidates and PMI scores",
            "/join-from-bridge": "POST - Perform join using a pre-computed bridge table",
        },
        "workflow": [
            "1. POST /bridge-table → Get all candidates with PMI scores",
            "2. POST /join-from-bridge → Select best matches from bridge table"
        ]
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.post("/bridge-table", response_model=BridgeTableResponse)
async def create_bridge_table(request_data: BridgeTableRequest, request: Request):
    """
    Create a bridge table with all candidate matches and PMI scores.
    
    This endpoint generates all possible matches between two lists based on
    corpus co-occurrence data, with PMI scores indicating match confidence.
    
    Args:
        request_data: BridgeTableRequest containing two lists (list_r and list_s)
        request: FastAPI request object to access app state
    
    Returns:
        BridgeTableResponse with all candidate matches and their PMI scores
        
    Raises:
        HTTPException: If the operation fails
    """
    try:
        join_service: SemanticJoinService = request.app.state.join_service
        bridge_table = join_service.create_bridge_table(
            request_data.list_r, 
            request_data.list_s
        )
        
        return BridgeTableResponse(
            bridge_table=bridge_table,
            total_r_values=len(request_data.list_r),
            total_s_values=len(request_data.list_s),
            total_candidates=len(bridge_table),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating bridge table: {str(e)}",
        )


@router.post("/join-from-bridge", response_model=JoinResponse)
async def join_from_bridge(request_data: JoinWithBridgeRequest, request: Request):
    """
    Perform a semantic join using a pre-computed bridge table.
    
    This endpoint takes a bridge table (from /bridge-table) and selects the
    best match for each R value based on PMI scores.
    
    Args:
        request_data: JoinWithBridgeRequest containing list_r and bridge_table
        request: FastAPI request object to access app state
    
    Returns:
        JoinResponse with mapping of R values to their best matching S values
        
    Raises:
        HTTPException: If the operation fails
    """
    try:
        join_service: SemanticJoinService = request.app.state.join_service
        
        # Convert Pydantic models to dicts
        bridge_table_dicts = [entry.model_dump() for entry in request_data.bridge_table]
        
        result = join_service.perform_join_from_bridge(
            request_data.list_r,
            bridge_table_dicts,
        )
        
        return JoinResponse(
            result=result,
            total_r_values=len(request_data.list_r),
            total_s_values=len(set(entry.s_val for entry in request_data.bridge_table)),
            matched_count=sum(1 for v in result.values() if v is not None),
            unmatched_count=sum(1 for v in result.values() if v is None),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing join from bridge: {str(e)}",
        )



