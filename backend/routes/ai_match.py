from fastapi import APIRouter, HTTPException, Request

from backend.models.ai_match import (
    AIColumnRecommendationRequest,
    AIColumnRecommendationResponse,
    AIOllamaStatus,
    AIBridgeRecommendationRequest,
    AIBridgeRecommendationResponse,
)
from backend.services.AIRecommendationService import AIRecommendationService


router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


@router.post("/recommend-columns", response_model=AIColumnRecommendationResponse)
async def recommend_columns(
    request_data: AIColumnRecommendationRequest, request: Request
):
    """Get AI recommendations for which columns to join."""
    try:
        ai_service = AIRecommendationService()

        status = ai_service.check_ollama_status()
        if not status.get("ollama_running"):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Ollama service is not available",
                    "recommendation": status.get(
                        "recommendation", "Start Ollama service"
                    ),
                    "details": status,
                },
            )

        if not status.get("model_available"):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Model '{ai_service.model}' is not available",
                    "recommendation": f"Pull the model with: ollama pull {ai_service.model}",
                    "available_models": status.get("available_models", []),
                },
            )

        result = ai_service.recommend_column_joins(
            table_r=request_data.table_r,
            table_s=request_data.table_s,
            max_samples=request_data.max_samples,
        )

        return AIColumnRecommendationResponse(**result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting AI recommendations: {str(e)}"
        )


@router.get("/status", response_model=AIOllamaStatus)
async def check_ai_status():
    """Check if Ollama is running and which models are available."""
    ai_service = AIRecommendationService()
    status = ai_service.check_ollama_status()
    return AIOllamaStatus(**status)


@router.post("/recommend-bridge-entries", response_model=AIBridgeRecommendationResponse)
async def recommend_bridge_entries(request_data: AIBridgeRecommendationRequest):
    """Get AI recommendations for which bridge entries to use."""
    try:
        ai_service = AIRecommendationService()

        status = ai_service.check_ollama_status()
        if not status.get("ollama_running"):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Ollama service is not available",
                    "recommendation": status.get(
                        "recommendation", "Start Ollama service"
                    ),
                    "details": status,
                },
            )

        if not status.get("model_available"):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Model '{ai_service.model}' is not available",
                    "recommendation": f"Pull the model with: ollama pull {ai_service.model}",
                    "available_models": status.get("available_models", []),
                },
            )

        result = ai_service.recommend_bridge_entries(
            bridge_entries=[
                entry.dict() if hasattr(entry, "dict") else entry
                for entry in request_data.bridge_entries
            ]
        )

        return AIBridgeRecommendationResponse(**result)

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
