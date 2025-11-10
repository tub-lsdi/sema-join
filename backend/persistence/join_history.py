from sqlalchemy import Column, Integer, DateTime, func, ForeignKey, String
from sqlalchemy.orm import Session, relationship

from .base import Base
import json


class JoinHistory(Base):
    __tablename__ = "join_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_r_entry_id = Column(Integer, ForeignKey("table_entry.id"), nullable=False)
    list_s_entry_id = Column(Integer, ForeignKey("table_entry.id"), nullable=False)
    bridge_table_entry_id = Column(
        Integer, ForeignKey("table_entry.id"), nullable=False
    )
    result_entry_id = Column(Integer, ForeignKey("table_entry.id"), nullable=False)
    r_join_col = Column(String(64), nullable=False)
    s_join_col = Column(String(64), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    list_r_entry = relationship("TableEntry", foreign_keys=[list_r_entry_id])
    list_s_entry = relationship("TableEntry", foreign_keys=[list_s_entry_id])
    bridge_table_entry = relationship(
        "TableEntry", foreign_keys=[bridge_table_entry_id]
    )
    result_entry = relationship("TableEntry", foreign_keys=[result_entry_id])


def create_join_history(
    session: Session,
    list_r_entry,
    list_s_entry,
    bridge_table_entry,
    result_entry,
    r_join_col: str,
    s_join_col: str,
) -> JoinHistory:
    """Create a JoinHistory record linking four TableEntry rows.

    Each of the four entry parameters may be either an integer id or an object
    with an `id` attribute (for example the `TableEntry` ORM instance).

    Returns the created JoinHistory instance (refreshed).
    """

    def _extract_id(val, name: str) -> int:
        if isinstance(val, int):
            return val
        if hasattr(val, "id"):
            return int(getattr(val, "id"))
        raise ValueError(
            f"{name} must be an int id or an object with an 'id' attribute"
        )

    list_r_id = _extract_id(list_r_entry, "list_r_entry")
    list_s_id = _extract_id(list_s_entry, "list_s_entry")
    bridge_id = _extract_id(bridge_table_entry, "bridge_table_entry")
    result_id = _extract_id(result_entry, "result_entry")

    join_history = JoinHistory(
        list_r_entry_id=list_r_id,
        list_s_entry_id=list_s_id,
        bridge_table_entry_id=bridge_id,
        result_entry_id=result_id,
        r_join_col=r_join_col,
        s_join_col=s_join_col,
    )

    session.add(join_history)
    try:
        session.commit()
        session.refresh(join_history)
        return join_history
    except Exception:
        session.rollback()
        raise


def get_entire_join_history(session: Session) -> list[JoinHistory]:
    return session.query(JoinHistory).order_by(JoinHistory.created_at.desc()).all()


def get_join_history_with_bodies(session: Session, history_id: int):
    """Return a JoinHistory row by id along with parsed table bodies.

    Returns a tuple (join_history, bodies_dict) where bodies_dict contains
    keys: list_r, list_s, bridge_table, result each mapped to the parsed
    JSON body (a list of dicts). If the history row is not found, returns
    (None, None).
    """
    row = (
        session.query(JoinHistory)
        .filter(JoinHistory.id == int(history_id))
        .one_or_none()
    )
    if row is None:
        return None, None

    def _parse_body(table_entry):
        if table_entry is None:
            return []
        try:
            return json.loads(table_entry.body)
        except Exception:
            return []

    bodies = {
        "list_r": _parse_body(row.list_r_entry),
        "list_s": _parse_body(row.list_s_entry),
        "bridge_table": _parse_body(row.bridge_table_entry),
        "result": _parse_body(row.result_entry),
    }

    return row, bodies
