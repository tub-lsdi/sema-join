"""
History endpoints.
"""

from fastapi import APIRouter, Request, HTTPException
from backend.models.history import HistoryResponse, HistoryEntry
from backend.persistence.join_history import get_entire_join_history

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
