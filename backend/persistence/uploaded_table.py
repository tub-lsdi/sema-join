import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from backend.persistence import Base


class UploadedTable(Base):
    __tablename__ = "uploaded_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    upload_timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    body = Column(Text, nullable=False)
    columns = Column(JSON, nullable=False)


def create_uploaded_table(
    session: Session,
    body: List[dict],
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> UploadedTable:
    """Create a new uploaded table in the database."""
    if not body or not all(isinstance(item, dict) for item in body):
        raise ValueError("body must be a non-empty list of dicts")

    columns = list({key for item in body for key in item.keys()})

    try:
        body_str = json.dumps(body)
    except TypeError as e:
        raise ValueError("body must be JSON serializable") from e

    if not name:
        name = f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    table = UploadedTable(
        name=name, description=description, body=body_str, columns=columns
    )
    session.add(table)

    try:
        session.commit()
        session.refresh(table)
        return table
    except Exception:
        session.rollback()
        raise


def list_uploaded_tables(session: Session) -> List[UploadedTable]:
    """List all uploaded tables, ordered by upload timestamp descending."""
    return (
        session.query(UploadedTable)
        .order_by(UploadedTable.upload_timestamp.desc())
        .all()
    )


def get_uploaded_table_by_id(
    session: Session, table_id: int
) -> Optional[UploadedTable]:
    """Get an uploaded table by ID."""
    return session.query(UploadedTable).filter(UploadedTable.id == table_id).first()


def delete_uploaded_table(session: Session, table_id: int) -> bool:
    """Delete an uploaded table by ID. Returns True if deleted, False if not found."""
    table = get_uploaded_table_by_id(session, table_id)
    if not table:
        return False

    session.delete(table)
    session.commit()
    return True


def get_uploaded_table_body(table: UploadedTable) -> List[Dict[str, Any]]:
    """Parse and return the body of an uploaded table."""
    return json.loads(table.body)
