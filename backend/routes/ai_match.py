from fastapi import APIRouter, HTTPException, Request

from backend.models.ai_match import (
    AIColumnMatchRequest,
    AIColumnMatchResponse,
    OllamaStatusResponse,
    BridgeEntrySuggestionRequest,
    BridgeEntrySuggestionResponse,
)
from backend.services.AIColumnMatchingService import AIColumnMatchingService


router = APIRouter(
    prefix="/ai",
    tags=["ai-matching"],
)


@router.post("/match-columns", response_model=AIColumnMatchResponse)
async def match_columns_with_ai(request_data: AIColumnMatchRequest, request: Request):
    """
    Select the best match for column based on semantic similarity.

    Args:
        request_data: AIColumnMatchRequest containing:
            - table_r: First table as list of records
            - table_s: Second table as list of records
            - max_samples: Number of rows to analyze from each table (default: 100)
        request: FastAPI request object to access app state

    Returns:
        AIColumnMatchResponse with:
            - recommended_joins: List of column pairs to join
            - analysis: Overall analysis of table relationship
            - model_used: Name of AI model used

    Raises:
        HTTPException: If Ollama is not available or analysis fails
    """
    try:
        ai_service = AIColumnMatchingService()

        # Check if Ollama is running first
        status = ai_service.check_ollama_status()
        if not status.get("ollama_running"):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Ollama service is not available",
                    "suggestion": status.get("suggestion", "Start Ollama service"),
                    "details": status,
                },
            )

        if not status.get("model_available"):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Model '{ai_service.model}' is not available",
                    "suggestion": f"Pull the model with: ollama pull {ai_service.model}",
                    "available_models": status.get("available_models", []),
                },
            )

        # Get recommendations from AI
        result = ai_service.recommend_column_joins(
            table_r=request_data.table_r,
            table_s=request_data.table_s,
            max_samples=request_data.max_samples,
        )

        return AIColumnMatchResponse(**result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting AI recommendations: {str(e)}"
        )


@router.get("/status", response_model=OllamaStatusResponse)
async def check_ai_status():
    """
    Check if Ollama is running and which models are available.

    This endpoint helps diagnose issues with the AI service by checking:
    - Whether Ollama is running
    - Which models are available
    - Whether the configured model is ready to use

    Returns:
        OllamaStatusResponse with status information
    """
    ai_service = AIColumnMatchingService()
    status = ai_service.check_ollama_status()
    return OllamaStatusResponse(**status)


@router.post("/suggest-bridge-entries", response_model=BridgeEntrySuggestionResponse)
async def suggest_best_bridge_entries(request_data: BridgeEntrySuggestionRequest):
    """
    Select the best match for each R value from RS-JP top-k results.

    Args:
        request_data: BridgeEntrySuggestionRequest containing:
            - bridge_entries: List of RS-JP results with r_val, s_val, npmi

    Returns:
        BridgeEntrySuggestionResponse with:
            - selections: Best S value for each R value with reasoning
            - analysis: Overall explanation
            - selected_indices: Indices to select in the original array
            - model_used: AI model name

    Raises:
        HTTPException: If Ollama is not available or analysis fails
    """
    try:
        ai_service = AIColumnMatchingService()

        # Check if Ollama is running
        status = ai_service.check_ollama_status()
        if not status.get("ollama_running"):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Ollama service is not available",
                    "suggestion": status.get("suggestion", "Start Ollama service"),
                    "details": status,
                },
            )

        if not status.get("model_available"):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Model '{ai_service.model}' is not available",
                    "suggestion": f"Pull the model with: ollama pull {ai_service.model}",
                    "available_models": status.get("available_models", []),
                },
            )

        # Get AI suggestions
        result = ai_service.suggest_best_bridge_entries(
            bridge_entries=[
                entry.dict() if hasattr(entry, "dict") else entry
                for entry in request_data.bridge_entries
            ]
        )

        return BridgeEntrySuggestionResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid input or AI response: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting AI suggestions: {str(e)}"
        )
