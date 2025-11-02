"""
Join operation endpoints.
"""

from fastapi import APIRouter, HTTPException, Request

from backend.models import JoinResponse, JoinWithBridgeRequest
from backend.services import SemanticJoinService
from backend.persistence.table_entry import create_table_entry
from backend.persistence.join_history import create_join_history


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
        bridge_table_dicts = [entry.model_dump() for entry in request_data.bridge_table]

        # Perform three-way join
        result = join_service.perform_join_from_bridge(
            list_r=request_data.list_r,
            r_join_col=request_data.r_join_col,
            bridge_table=bridge_table_dicts,
            list_s=request_data.list_s,
            s_join_col=request_data.s_join_col,
        )

        # Persist the input and output tables to the application DB if available
        try:
            Session = request.app.state.app_db_sessionmaker
            db_session = Session()
            try:
                list_r_entry = create_table_entry(db_session, request_data.list_r)
                list_s_entry = create_table_entry(db_session, request_data.list_s)
                bridge_table_entry = create_table_entry(db_session, bridge_table_dicts)
                result_entry = create_table_entry(db_session, result)
                create_join_history(
                    session=db_session,
                    list_r_entry=list_r_entry,
                    list_s_entry=list_s_entry,
                    bridge_table_entry=bridge_table_entry,
                    result_entry=result_entry,
                    r_join_col=request_data.r_join_col,
                    s_join_col=request_data.s_join_col,
                )
            finally:
                db_session.close()
        except Exception as e:
            # If persistence fails, continue but log the issue by raising a HTTPException
            raise HTTPException(
                status_code=500,
                detail=f"Error saving uploaded tables to DB: {str(e)}",
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
