from sqlalchemy import Column, Integer, Text, JSON, DateTime, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import LONGTEXT
from typing import List
import json

from .base import Base


class TableEntry(Base):
    __tablename__ = "table_entry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(LONGTEXT, nullable=False)
    columns = Column(JSON, nullable=False)


def create_table_entry(session: Session, body: List[dict]) -> TableEntry:
    if (
        not isinstance(body, list)
        or len(body) == 0
        or any(not isinstance(item, dict) for item in body)
    ):
        raise ValueError("`body` must be a non-empty list of dicts")

    key_set = set()
    for item in body:
        key_set.update(item.keys())

    try:
        body_str = json.dumps(body)
    except TypeError as e:
        raise ValueError("`body` must be JSON serializable") from e

    columns = list(key_set)
    table_entry = TableEntry(body=body_str, columns=columns)
    session.add(table_entry)
    try:
        session.commit()
        session.refresh(table_entry)
        return table_entry
    except Exception:
        session.rollback()
        raise
