from sqlalchemy import Column, Integer, Text, JSON, DateTime, func, String
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from .base import Base


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
    return (
        session.query(UploadedTable)
        .order_by(UploadedTable.upload_timestamp.desc())
        .all()
    )


def get_uploaded_table_by_id(
    session: Session, table_id: int
) -> Optional[UploadedTable]:
    return (
        session.query(UploadedTable).filter(UploadedTable.id == table_id).one_or_none()
    )


def delete_uploaded_table(session: Session, table_id: int) -> bool:
    table = get_uploaded_table_by_id(session, table_id)
    if not table:
        return False

    try:
        session.delete(table)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise


def get_uploaded_table_body(table: UploadedTable) -> List[dict]:
    try:
        return json.loads(table.body)
    except Exception:
        return []
