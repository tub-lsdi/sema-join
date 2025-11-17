from pydantic import BaseModel
from typing import Optional, List


class UploadedTableMetadata(BaseModel):
    """Metadata about an uploaded table (without body data)."""

    id: int
    name: str
    description: Optional[str]
    upload_timestamp: str
    columns: List[str]
    row_count: int


class UploadedTableDetail(UploadedTableMetadata):
    """Full uploaded table including body data."""

    body: List[dict]


class UploadTableResponse(BaseModel):
    """Response after uploading a table."""

    id: int
    name: str
    message: str


class TablesListResponse(BaseModel):
    """Response listing all uploaded tables."""

    tables: List[UploadedTableMetadata]
    total: int
