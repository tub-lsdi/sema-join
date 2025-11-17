from pydantic import BaseModel, Field


class AIColumnRecommendation(BaseModel):
    """AI recommendation for which columns to join."""

    r_column: str = Field(..., description="Column name from table R")
    s_column: str = Field(..., description="Column name from table S")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    reason: str = Field(
        ..., description="Explanation for why these columns should be joined"
    )


class AIColumnRecommendationRequest(BaseModel):
    """Request for AI column recommendations."""

    table_r: list[dict] = Field(
        ...,
        description="First table as list of records",
        min_length=1,
        examples=[
            [
                {"id": 1, "country_code": "US", "population": 331000000},
                {"id": 2, "country_code": "UK", "population": 67000000},
            ]
        ],
    )
    table_s: list[dict] = Field(
        ...,
        description="Second table as list of records",
        min_length=1,
        examples=[
            [
                {"country_name": "United States", "continent": "North America"},
                {"country_name": "United Kingdom", "continent": "Europe"},
            ]
        ],
    )
    max_samples: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of rows to analyze from each table (default: 100)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "table_r": [
                        {"id": 1, "country_code": "US", "population": 331000000},
                        {"id": 2, "country_code": "UK", "population": 67000000},
                        {"id": 3, "country_code": "FR", "population": 67000000},
                    ],
                    "table_s": [
                        {"country_name": "United States", "continent": "North America"},
                        {"country_name": "United Kingdom", "continent": "Europe"},
                        {"country_name": "France", "continent": "Europe"},
                    ],
                    "max_samples": 100,
                }
            ]
        }
    }


class AIColumnRecommendationResponse(BaseModel):
    """AI-powered column join recommendations."""

    recommendations: list[AIColumnRecommendation] = Field(
        ..., description="List of recommended column join pairs"
    )
    analysis: str = Field(..., description="Overall analysis of the table relationship")
    model_used: str = Field(..., description="Name of the AI model used for analysis")
    table_r_columns: list[str] = Field(..., description="Column names from table R")
    table_s_columns: list[str] = Field(..., description="Column names from table S")
    rows_analyzed_r: int = Field(
        ..., description="Number of rows analyzed from table R"
    )
    rows_analyzed_s: int = Field(
        ..., description="Number of rows analyzed from table S"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "recommendations": [
                        {
                            "r_column": "country_code",
                            "s_column": "country_name",
                            "confidence": 0.92,
                            "reason": "country_code contains abbreviations that semantically match country_name full names",
                        }
                    ],
                    "analysis": "Table R contains country data with ISO codes, while Table S has full country names. These can be semantically joined.",
                    "model_used": "mistral",
                    "table_r_columns": ["id", "country_code", "population"],
                    "table_s_columns": ["country_name", "continent"],
                    "rows_analyzed_r": 100,
                    "rows_analyzed_s": 100,
                }
            ]
        }
    }


class AIOllamaStatus(BaseModel):
    """Ollama AI service status."""

    ollama_running: bool = Field(..., description="Whether Ollama service is running")
    model_requested: str | None = Field(
        default=None, description="Model requested for use"
    )
    model_available: bool | None = Field(
        default=None, description="Whether the requested model is available"
    )
    available_models: list[str] | None = Field(
        default=None, description="List of available model names"
    )
    error: str | None = Field(
        default=None, description="Error message if Ollama is not running"
    )
    recommendation: str | None = Field(
        default=None, description="Recommendation for fixing the issue"
    )


class AIBridgeRecommendation(BaseModel):
    """AI recommendation for which S value to use for an R value."""

    r_val: str = Field(..., description="Value from R")
    recommended_s_val: str = Field(
        ..., description="Recommended S value for this R value"
    )
    reason: str = Field(..., description="Why this S value was recommended")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in this recommendation"
    )


class AIBridgeRecommendationRequest(BaseModel):
    """Request for AI bridge entry recommendations."""

    bridge_entries: list[dict] = Field(
        ...,
        description="RS-JP top-k results with r_val, s_val, npmi fields",
        min_length=1,
        examples=[
            [
                {"r_val": "Germany", "s_val": "DE", "npmi": 0.9},
                {"r_val": "Germany", "s_val": "GE", "npmi": 0.7},
                {"r_val": "UK", "s_val": "GB", "npmi": 0.95},
            ]
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bridge_entries": [
                        {"r_val": "Germany", "s_val": "DE", "npmi": 0.9},
                        {"r_val": "Germany", "s_val": "GE", "npmi": 0.7},
                        {"r_val": "Germany", "s_val": "GER", "npmi": 0.5},
                        {"r_val": "UK", "s_val": "GB", "npmi": 0.95},
                        {"r_val": "UK", "s_val": "UK", "npmi": 0.8},
                    ]
                }
            ]
        }
    }


class AIBridgeRecommendationResponse(BaseModel):
    """AI recommendations for bridge entries."""

    recommendations: list[AIBridgeRecommendation] = Field(
        ..., description="Recommended S value for each R value"
    )
    analysis: str = Field(..., description="Overall reasoning for the recommendations")
    recommended_indices: list[int] = Field(
        ...,
        description="Indices of recommended entries in the original bridge_entries array",
    )
    model_used: str = Field(..., description="Name of AI model used")
