from pydantic import BaseModel
from typing import Optional, List


class UploadedTableMetadata(BaseModel):
    id: int
    name: str
    description: Optional[str]
    upload_timestamp: str
    columns: List[str]
    row_count: int


class UploadedTableDetail(UploadedTableMetadata):
    body: List[dict]


class UploadTableResponse(BaseModel):
    id: int
    name: str
    message: str


class TablesListResponse(BaseModel):
    tables: List[UploadedTableMetadata]
    total: int
