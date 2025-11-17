"""
Join operation models for semantic join API.
"""

from pydantic import BaseModel, Field
from .bridge import BridgeTableEntry


class JoinWithBridgeRequest(BaseModel):
    """Request model for three-way join using table IDs from database."""

    table_r_id: int = Field(
        ...,
        description="ID of uploaded table R from database",
        examples=[1],
    )
    r_join_col: str = Field(
        ...,
        description="Column name in table R to join with bridge table r_val",
        examples=["country_code"],
    )
    bridge_table: list[BridgeTableEntry] = Field(
        ...,
        description="Pre-computed bridge table with candidates and PMI scores",
        min_length=1,
    )
    table_s_id: int = Field(
        ...,
        description="ID of uploaded table S from database",
        examples=[2],
    )
    s_join_col: str = Field(
        ...,
        description="Column name in table S to join with bridge table s_val",
        examples=["country_name"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "table_r_id": 1,
                    "r_join_col": "country_code",
                    "bridge_table": [
                        {"r_val": "US", "s_val": "USA", "pmi": 5.32},
                        {"r_val": "UK", "s_val": "United Kingdom", "pmi": 6.12},
                    ],
                    "table_s_id": 2,
                    "s_join_col": "country_name",
                }
            ]
        }
    }


class JoinResponse(BaseModel):
    """Response model for the three-way semantic join endpoint."""

    result: list[dict] = Field(
        ...,
        description="List of joined records (R JOIN bridge JOIN S)",
    )
    total_records: int = Field(
        ...,
        description="Total number of records in the result",
    )
    total_r_records: int = Field(
        ...,
        description="Total number of records in list R",
    )
    matched_count: int = Field(
        ...,
        description="Number of R records that found a match in S",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result": [
                        {
                            "id": 1,
                            "country_code": "US",
                            "r_val": "US",
                            "s_val": "USA",
                            "pmi": 5.32,
                            "country_name": "USA",
                            "population": 331000000,
                        },
                        {
                            "id": 2,
                            "country_code": "UK",
                            "r_val": "UK",
                            "s_val": "United Kingdom",
                            "pmi": 6.12,
                            "country_name": "United Kingdom",
                            "population": 67000000,
                        },
                    ],
                    "total_records": 2,
                    "total_r_records": 2,
                    "matched_count": 2,
                }
            ]
        }
    }
