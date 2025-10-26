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
        description="All candidate matches with PMI scores",
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
        description="Total number of candidate matches found",
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
    """Request model for joining with a pre-computed bridge table."""
    
    list_r: list[str] = Field(
        ...,
        description="First list of strings (R set)",
        min_length=1,
        examples=[["US", "UK", "DE"]],
    )
    bridge_table: list[BridgeTableEntry] = Field(
        ...,
        description="Pre-computed bridge table with candidates and PMI scores",
        min_length=1,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "list_r": ["US", "UK"],
                    "bridge_table": [
                        {"r_val": "US", "s_val": "USA", "pmi": 5.32},
                        {"r_val": "UK", "s_val": "United Kingdom", "pmi": 6.12},
                    ],
                }
            ]
        }
    }


class JoinResponse(BaseModel):
    """Response model for the semantic join endpoint."""
    
    result: dict[str, Optional[str]] = Field(
        ...,
        description="Mapping of R values to their best matching S values (or null if no match)",
    )
    total_r_values: int = Field(
        ...,
        description="Total number of values in list R",
    )
    total_s_values: int = Field(
        ...,
        description="Total number of values in list S",
    )
    matched_count: int = Field(
        ...,
        description="Number of R values that found a match in S",
    )
    unmatched_count: int = Field(
        ...,
        description="Number of R values that did not find a match in S",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result": {
                        "US": "USA",
                        "UK": "United Kingdom",
                        "DE": "Germany",
                    },
                    "total_r_values": 3,
                    "total_s_values": 3,
                    "matched_count": 3,
                    "unmatched_count": 0,
                }
            ]
        }
    }
