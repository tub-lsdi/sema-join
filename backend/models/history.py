from pydantic import BaseModel, Field
from datetime import datetime


class HistoryEntry(BaseModel):
    id: int = Field(..., description="Unique history record id")
    timestamp: datetime = Field(..., description="When the join was created")
    r_join_col: str = Field(..., description="Join column used for R")
    s_join_col: str = Field(..., description="Join column used for S")


class HistoryResponse(BaseModel):
    entries: list[HistoryEntry] = Field(
        ..., description="List of saved join operations"
    )

    class Config:
        orm_mode = True


class HistoryDetailEntry(HistoryEntry):
    list_r: list[dict] = Field(..., description="Body of the stored R table")
    list_s: list[dict] = Field(..., description="Body of the stored S table")
    bridge_table: list[dict] = Field(..., description="Body of the stored bridge table")
    result: list[dict] = Field(..., description="Body of the stored result table")
