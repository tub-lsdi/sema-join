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
            "/bridge-table": "POST - Create bridge table with highest PMI matches",
            "/join-from-bridge": "POST - Perform three-way join (R ⋈ bridge ⋈ S)",
        },
        "workflow": [
            "1. POST /bridge-table → Get best match for each R value (highest PMI)",
            "2. POST /join-from-bridge → Three-way join: list_r ⋈ bridge_table ⋈ list_s"
        ]
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.post("/bridge-table", response_model=BridgeTableResponse)
async def create_bridge_table(request_data: BridgeTableRequest, request: Request):
    """
    Create a bridge table with the highest PMI match for each R value.

    This endpoint finds the best match for each value in list_r from list_s
    based on corpus co-occurrence data, with PMI scores indicating match confidence.
    Only the candidate with the highest PMI score per R value is returned.

    Args:
        request_data: BridgeTableRequest containing two lists (list_r and list_s)
        request: FastAPI request object to access app state

    Returns:
        BridgeTableResponse with the highest PMI match for each R value

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
    Perform a three-way semantic join using a bridge table.

    This endpoint performs: list_r JOIN bridge_table JOIN list_s
    The bridge table connects R and S records using the specified join columns.

    Args:
        request_data: JoinWithBridgeRequest containing:
            - list_r: records from R dataset
            - r_join_col: column in R to join with bridge table
            - bridge_table: bridge with r_val, s_val, pmi
            - list_s: records from S dataset
            - s_join_col: column in S to join with bridge table
        request: FastAPI request object to access app state

    Returns:
        JoinResponse with joined records from all three tables

    Raises:
        HTTPException: If the operation fails
    """
    try:
        join_service: SemanticJoinService = request.app.state.join_service

        # Convert Pydantic models to dicts
        bridge_table_dicts = [entry.model_dump()
                              for entry in request_data.bridge_table]

        # Perform three-way join
        result = join_service.perform_join_from_bridge(
            list_r=request_data.list_r,
            r_join_col=request_data.r_join_col,
            bridge_table=bridge_table_dicts,
            list_s=request_data.list_s,
            s_join_col=request_data.s_join_col,
        )

        return JoinResponse(
            result=result,
            total_records=len(result),
            total_r_records=len(request_data.list_r),
            matched_count=len(result),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing join from bridge: {str(e)}",
        )
