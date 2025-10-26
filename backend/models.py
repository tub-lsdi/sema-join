"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class BridgeTableRequest(BaseModel):
    """Request model for creating a bridge table."""
    
    list_r: list[str] = Field(
        ...,
        description="First list of strings (R set)",
        min_length=1,
        examples=[["US", "UK", "DE"]],
    )
    list_s: list[str] = Field(
        ...,
        description="Second list of strings (S set)",
        min_length=1,
        examples=[["USA", "United Kingdom", "Germany"]],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "list_r": ["US", "UK", "DE"],
                    "list_s": ["USA", "United Kingdom", "Germany"],
                }
            ]
        }
    }


class BridgeTableEntry(BaseModel):
    """Single entry in the bridge table showing a candidate match."""
    
    r_val: str = Field(..., description="Value from list R")
    s_val: str = Field(..., description="Candidate value from list S")
    pmi: float = Field(..., description="PMI score (confidence) for this match")


class BridgeTableResponse(BaseModel):
    """Response model for bridge table creation."""
    
    bridge_table: list[BridgeTableEntry] = Field(
        ...,
        description="Best match for each R value (highest PMI score)",
    )
    total_r_values: int = Field(
        ...,
        description="Total number of values in list R",
    )
    total_s_values: int = Field(
        ...,
        description="Total number of values in list S",
    )
    total_candidates: int = Field(
        ...,
        description="Total number of matches found (one per R value)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bridge_table": [
                        {"r_val": "US", "s_val": "USA", "pmi": 5.32},
                        {"r_val": "US", "s_val": "United States", "pmi": 4.81},
                        {"r_val": "UK", "s_val": "United Kingdom", "pmi": 6.12},
                    ],
                    "total_r_values": 2,
                    "total_s_values": 3,
                    "total_candidates": 3,
                }
            ]
        }
    }


class JoinWithBridgeRequest(BaseModel):
    """Request model for three-way join with a pre-computed bridge table."""
    
    list_r: list[dict] = Field(
        ...,
        description="First list of records (R dataset)",
        min_length=1,
        examples=[[{"id": 1, "country_code": "US"}, {"id": 2, "country_code": "UK"}]],
    )
    r_join_col: str = Field(
        ...,
        description="Column name in list_r to join with bridge table r_val",
        examples=["country_code"],
    )
    bridge_table: list[BridgeTableEntry] = Field(
        ...,
        description="Pre-computed bridge table with candidates and PMI scores",
        min_length=1,
    )
    list_s: list[dict] = Field(
        ...,
        description="Second list of records (S dataset)",
        min_length=1,
        examples=[[{"country_name": "USA", "population": 331000000}]],
    )
    s_join_col: str = Field(
        ...,
        description="Column name in list_s to join with bridge table s_val",
        examples=["country_name"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "list_r": [
                        {"id": 1, "country_code": "US"},
                        {"id": 2, "country_code": "UK"}
                    ],
                    "r_join_col": "country_code",
                    "bridge_table": [
                        {"r_val": "US", "s_val": "USA", "pmi": 5.32},
                        {"r_val": "UK", "s_val": "United Kingdom", "pmi": 6.12},
                    ],
                    "list_s": [
                        {"country_name": "USA", "population": 331000000},
                        {"country_name": "United Kingdom", "population": 67000000}
                    ],
                    "s_join_col": "country_name"
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
                            "population": 331000000
                        },
                        {
                            "id": 2,
                            "country_code": "UK",
                            "r_val": "UK",
                            "s_val": "United Kingdom",
                            "pmi": 6.12,
                            "country_name": "United Kingdom",
                            "population": 67000000
                        }
                    ],
                    "total_records": 2,
                    "total_r_records": 2,
                    "matched_count": 2,
                }
            ]
        }
    }
