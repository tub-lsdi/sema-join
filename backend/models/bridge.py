"""
Bridge table models for semantic join API.
"""
from pydantic import BaseModel, Field
from typing import Literal


class BridgeTableEntry(BaseModel):
    """Single entry in the bridge table showing a candidate match."""

    r_val: str = Field(..., description="Value from list R")
    s_val: str = Field(..., description="Candidate value from list S")
    pmi: float = Field(...,
                       description="PMI score (confidence) for this match")
    npmi: float | None = Field(
        description="NMPI score (confidence) for this match")


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
    join_method: Literal["row", "column"] = Field(
        default="row",
        description="Join algorithm: 'row' for RS-JP or 'column' for CS-JP-LP",
        examples=["row"],
    )
    top_k: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Number of top candidates to return per R value",
        examples=[5],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "list_r": ["US", "UK", "DE"],
                    "list_s": ["USA", "United Kingdom", "Germany"],
                    "join_method": "row",
                    "top_k": 5,
                }
            ]
        }
    }


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

