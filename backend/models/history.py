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
