"""
RS-JP algorithm implementation.
"""

from typing import Optional
from loguru import logger
from backend.services.PMIService import PMIService
from backend.config import settings
from .base import BridgeAlgorithm


class RSJPAlgorithm(BridgeAlgorithm):
    """
    RS-JP algorithm.

    Greedy algorithm: Each r independently picks its best s based on row-level PMI.
    Fast and efficient for most use cases.
    """

    def __init__(self, db_connection, pmi_service: Optional[PMIService] = None):
        """
        Initialize RS-JP algorithm.

        Args:
            db_connection: DuckDB connection (kept for compatibility, not used if pmi_service is provided)
            pmi_service: Optional PMIService instance. If not provided, creates one with default config.
        """
        super().__init__(db_connection, pmi_service)
        if self.pmi_service is None:
            self.pmi_service = PMIService(settings.GO_SERVICE_URL)

    def create_bridge(
        self,
        list_r: list[str],
        list_s: list[str],
        top_k: int = 1,
    ) -> list[dict]:
        """
        Create a bridge table using RS-JP algorithm.

        Greedy algorithm: Each r independently picks its best s based on row-level PMI.

        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set
            top_k: Number of top candidates to return per R value

        Returns:
            List of dictionaries with r_val, s_val, and npmi (PMI) fields
        """
        logger.info(
            f"RS-JP: Fetching row-level PMI scores from Go service for |R|={len(list_r)}, |S|={len(list_s)}"
        )

        # Fetch row-level PMI scores from Go service
        pmi_scores = self.pmi_service.get_row_pmi_scores(list_r, list_s)

        logger.info(
            f"RS-JP: Retrieved {len(pmi_scores)} PMI scores, processing top-{top_k} per R value"
        )

        # Group by r_val and get top_k candidates for each
        r_to_candidates = {}
        for (r_val, s_val), pmi in pmi_scores.items():
            if r_val not in r_to_candidates:
                r_to_candidates[r_val] = []
            r_to_candidates[r_val].append({"s_val": s_val, "pmi": pmi})

        # Sort candidates for each r_val by PMI descending and take top_k
        results = []
        for r_val in list_r:
            if r_val in r_to_candidates:
                # Sort by PMI descending
                candidates = sorted(
                    r_to_candidates[r_val], key=lambda x: x["pmi"], reverse=True
                )
                # Take top_k
                for candidate in candidates[:top_k]:
                    results.append(
                        {
                            "r_val": r_val,
                            "s_val": candidate["s_val"],
                            "npmi": candidate["pmi"],  # Use 'npmi' field name for consistency
                        }
                    )
            else:
                logger.debug(f"RS-JP: No PMI scores found for r_val={r_val}")

        logger.info(f"RS-JP: Generated {len(results)} bridge table entries")

        return results
