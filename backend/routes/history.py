"""
History endpoints.
"""

from fastapi import APIRouter, Request, HTTPException
from backend.models.history import HistoryResponse, HistoryEntry, HistoryDetailEntry
from backend.persistence.join_history import (
    get_entire_join_history,
    get_join_history_with_bodies,
)

router = APIRouter(prefix="", tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history(request: Request):
    """Return recent join history from the application DB.

    If the application DB is not configured or an error occurs, an empty
    list is returned (or a 500 is raised on serious errors).
    """
    try:
        if not hasattr(request.app.state, "app_db_sessionmaker"):
            return HistoryResponse(entries=[])

        Session = request.app.state.app_db_sessionmaker
        db = Session()
        try:
            rows = get_entire_join_history(db)

            entries = [
                HistoryEntry(
                    id=int(r.id),
                    timestamp=r.created_at,
                    r_join_col=r.r_join_col,
                    s_join_col=r.s_join_col,
                )
                for r in rows
            ]

            return HistoryResponse(entries=entries)
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {e}")


@router.get("/history/{history_id}", response_model=HistoryDetailEntry)
async def get_history_detail(history_id: int, request: Request):
    """Return a single history entry including the stored table bodies.

    The response includes only the bodies of the stored tables (list of rows),
    not the stored column metadata.
    """
    try:
        if not hasattr(request.app.state, "app_db_sessionmaker"):
            raise HTTPException(status_code=404, detail="History not found")

        Session = request.app.state.app_db_sessionmaker
        db = Session()
        try:
            row, bodies = get_join_history_with_bodies(db, history_id)
            if row is None:
                raise HTTPException(status_code=404, detail="History not found")

            detail = HistoryDetailEntry(
                id=int(row.id),
                timestamp=row.created_at,
                r_join_col=row.r_join_col,
                s_join_col=row.s_join_col,
                list_r=bodies.get("list_r", []),
                list_s=bodies.get("list_s", []),
                bridge_table=bodies.get("bridge_table", []),
                result=bodies.get("result", []),
            )

            return detail
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching history detail: {e}"
        )
