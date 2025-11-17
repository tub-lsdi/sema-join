"""Semantic join endpoints."""

from fastapi import APIRouter, HTTPException, Request

from backend.models import JoinResponse, JoinWithBridgeRequest
from backend.services import SemanticJoinService


router = APIRouter(prefix="", tags=["join"])


@router.post("/join-from-bridge", response_model=JoinResponse)
async def join_from_bridge(request_data: JoinWithBridgeRequest, request: Request):
    """Perform semantic join using uploaded tables and bridge table."""
    join_service: SemanticJoinService = request.app.state.join_service

    try:
        bridge_table = [entry.model_dump() for entry in request_data.bridge_table]

        result, total_r_records = join_service.perform_join_from_bridge(
            table_r_id=request_data.table_r_id,
            r_join_col=request_data.r_join_col,
            bridge_table=bridge_table,
            table_s_id=request_data.table_s_id,
            s_join_col=request_data.s_join_col,
        )

        return JoinResponse(
            result=result,
            total_records=len(result),
            total_r_records=total_r_records,
            matched_count=len(result),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
