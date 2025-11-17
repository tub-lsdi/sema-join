"""
Join operation endpoints.
"""

from fastapi import APIRouter, HTTPException, Request

from backend.models import JoinResponse, JoinWithBridgeRequest
from backend.services import SemanticJoinService
from backend.persistence.table_entry import create_table_entry
from backend.persistence.join_history import create_join_history
from backend.persistence.uploaded_table import (
    get_uploaded_table_by_id,
    get_uploaded_table_body,
)


router = APIRouter(
    prefix="",
    tags=["join"],
)


@router.post("/join-from-bridge", response_model=JoinResponse)
async def join_from_bridge(request_data: JoinWithBridgeRequest, request: Request):
    Session = request.app.state.app_db_sessionmaker
    db_session = Session()

    try:
        table_r = get_uploaded_table_by_id(db_session, request_data.table_r_id)
        if not table_r:
            raise HTTPException(status_code=404, detail="Table R not found")

        table_s = get_uploaded_table_by_id(db_session, request_data.table_s_id)
        if not table_s:
            raise HTTPException(status_code=404, detail="Table S not found")

        list_r = get_uploaded_table_body(table_r)
        list_s = get_uploaded_table_body(table_s)
        bridge_table = [entry.model_dump() for entry in request_data.bridge_table]

        join_service: SemanticJoinService = request.app.state.join_service
        result = join_service.perform_join_from_bridge(
            list_r=list_r,
            r_join_col=request_data.r_join_col,
            bridge_table=bridge_table,
            list_s=list_s,
            s_join_col=request_data.s_join_col,
        )

        list_r_entry = create_table_entry(db_session, list_r)
        list_s_entry = create_table_entry(db_session, list_s)
        bridge_entry = create_table_entry(db_session, bridge_table)
        result_entry = create_table_entry(db_session, result)
        create_join_history(
            session=db_session,
            list_r_entry=list_r_entry,
            list_s_entry=list_s_entry,
            bridge_table_entry=bridge_entry,
            result_entry=result_entry,
            r_join_col=request_data.r_join_col,
            s_join_col=request_data.s_join_col,
        )

        return JoinResponse(
            result=result,
            total_records=len(result),
            total_r_records=len(list_r),
            matched_count=len(result),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()
