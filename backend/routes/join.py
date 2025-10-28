"""
Join operation endpoints.
"""
from fastapi import APIRouter, HTTPException, Request

from backend.models import JoinResponse, JoinWithBridgeRequest
from backend.services import SemanticJoinService


router = APIRouter(
    prefix="",
    tags=["join"],
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
