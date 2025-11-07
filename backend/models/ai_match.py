from pydantic import BaseModel, Field


class ColumnJoinRecommendation(BaseModel):
    """A single column join recommendation from the AI."""

    r_column: str = Field(
        ...,
        description="Column name from table R"
    )
    s_column: str = Field(
        ...,
        description="Column name from table S"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    reason: str = Field(
        ...,
        description="Explanation for why these columns should be joined"
    )


class AIColumnMatchRequest(BaseModel):
    """Request model for AI-powered column matching."""

    table_r: list[dict] = Field(
        ...,
        description="First table as list of records",
        min_length=1,
        examples=[[
            {"id": 1, "country_code": "US", "population": 331000000},
            {"id": 2, "country_code": "UK", "population": 67000000}
        ]]
    )
    table_s: list[dict] = Field(
        ...,
        description="Second table as list of records",
        min_length=1,
        examples=[[
            {"country_name": "United States", "continent": "North America"},
            {"country_name": "United Kingdom", "continent": "Europe"}
        ]]
    )
    max_samples: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of rows to analyze from each table (default: 100)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "table_r": [
                        {"id": 1, "country_code": "US", "population": 331000000},
                        {"id": 2, "country_code": "UK", "population": 67000000},
                        {"id": 3, "country_code": "FR", "population": 67000000}
                    ],
                    "table_s": [
                        {"country_name": "United States",
                            "continent": "North America"},
                        {"country_name": "United Kingdom", "continent": "Europe"},
                        {"country_name": "France", "continent": "Europe"}
                    ],
                    "max_samples": 100
                }
            ]
        }
    }


class AIColumnMatchResponse(BaseModel):
    """Response model for AI-powered column matching."""

    recommended_joins: list[ColumnJoinRecommendation] = Field(
        ...,
        description="List of recommended column join pairs"
    )
    analysis: str = Field(
        ...,
        description="Overall analysis of the table relationship"
    )
    model_used: str = Field(
        ...,
        description="Name of the AI model used for analysis"
    )
    table_r_columns: list[str] = Field(
        ...,
        description="Column names from table R"
    )
    table_s_columns: list[str] = Field(
        ...,
        description="Column names from table S"
    )
    rows_analyzed_r: int = Field(
        ...,
        description="Number of rows analyzed from table R"
    )
    rows_analyzed_s: int = Field(
        ...,
        description="Number of rows analyzed from table S"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "recommended_joins": [
                        {
                            "r_column": "country_code",
                            "s_column": "country_name",
                            "confidence": 0.92,
                            "reason": "country_code contains abbreviations that semantically match country_name full names"
                        }
                    ],
                    "analysis": "Table R contains country data with ISO codes, while Table S has full country names. These can be semantically joined.",
                    "model_used": "mistral",
                    "table_r_columns": ["id", "country_code", "population"],
                    "table_s_columns": ["country_name", "continent"],
                    "rows_analyzed_r": 100,
                    "rows_analyzed_s": 100
                }
            ]
        }
    }


class OllamaStatusResponse(BaseModel):
    """Response model for Ollama status check."""

    ollama_running: bool = Field(
        ...,
        description="Whether Ollama service is running"
    )
    model_requested: str | None = Field(
        default=None,
        description="Model requested for use"
    )
    model_available: bool | None = Field(
        default=None,
        description="Whether the requested model is available"
    )
    available_models: list[str] | None = Field(
        default=None,
        description="List of available model names"
    )
    error: str | None = Field(
        default=None,
        description="Error message if Ollama is not running"
    )
    suggestion: str | None = Field(
        default=None,
        description="Suggestion for fixing the issue"
    )
