"""
Bridge table creation endpoints.
"""

from fastapi import APIRouter, HTTPException, Request

from backend.models import BridgeTableRequest, BridgeTableResponse
from backend.services import SemanticJoinService


router = APIRouter(
    prefix="",
    tags=["bridge"],
)


@router.post("/bridge-table", response_model=BridgeTableResponse)
async def create_bridge_table(request_data: BridgeTableRequest, request: Request):
    """
    Create a bridge table using RS-JP or CS-JP algorithm.

    This endpoint finds the best matches for each value in list_r from list_s
    based on corpus co-occurrence data.

    - RS-JP (row): Greedy algorithm, each R value independently picks best S
    - CS-JP (column): Optimization considering semantic compatibility

    Args:
        request_data: BridgeTableRequest containing:
            - list_r: values to be matched
            - list_s: candidate values
            - join_method: "row" for RS-JP or "column" for CS-JP
        request: FastAPI request object to access app state

    Returns:
        BridgeTableResponse with the best matches

    Raises:
        HTTPException: If the operation fails
    """
    try:
        join_service: SemanticJoinService = request.app.state.join_service
        bridge_table = join_service.create_bridge_table(
            request_data.list_r,
            request_data.list_s,
            request_data.join_method,
            request_data.top_k,
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
