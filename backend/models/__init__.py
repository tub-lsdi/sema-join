from .bridge import (
    BridgeTableEntry,
    BridgeTableRequest,
    BridgeTableResponse,
)
from .join import (
    JoinWithBridgeRequest,
    JoinResponse,
)
from .history import (
    HistoryEntry,
    HistoryResponse,
    HistoryDetailEntry,
)
from .ai_match import (
    AIColumnMatchRequest,
    AIColumnRecommendation,
    AIColumnRecommendationResponse,
    AIBridgeRecommendation,
    AIBridgeRecommendationRequest,
    AIBridgeRecommendationResponse,
    AIOllamaStatus,
)
from .uploaded_table import (
    UploadedTableMetadata,
    UploadedTableDetail,
    UploadTableResponse,
    TablesListResponse,
)

__all__ = [
    # Bridge models
    "BridgeTableEntry",
    "BridgeTableRequest",
    "BridgeTableResponse",
    # Join models
    "JoinWithBridgeRequest",
    "JoinResponse",
    # History models
    "HistoryEntry",
    "HistoryResponse",
    "HistoryDetailEntry",
    # AI recommendation models
    "AIColumnMatchRequest",
    "AIColumnRecommendation",
    "AIColumnRecommendationResponse",
    "AIBridgeRecommendation",
    "AIBridgeRecommendationRequest",
    "AIBridgeRecommendationResponse",
    "AIOllamaStatus",
    # Uploaded table models
    "UploadedTableMetadata",
    "UploadedTableDetail",
    "UploadTableResponse",
    "TablesListResponse",
]
