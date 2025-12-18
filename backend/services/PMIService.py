import os
import requests
from typing import Dict, Tuple
from loguru import logger


class PMIService:
    """
    Service for retrieving PMI scores from the Go service.

    The Go service calculates column-level PMI scores (w_ijkl) for quadruples
    (ri, sj, rk, sl) where:
    - ri, rk are from list R
    - sj, sl are from list S
    - The score indicates how strongly these values co-occur across tables
    """

    def __init__(self, go_service_url: str = None):
        if go_service_url is None:
            go_service_url = os.getenv("GO_SERVICE_URL", "http://localhost:8080")

        self.go_service_url = go_service_url.rstrip("/")
        self.calculate_endpoint = f"{self.go_service_url}/calculate-quad-scores"
        self.row_pmis_endpoint = f"{self.go_service_url}/row-pmis"
        logger.info(
            f"PMIService initialized with endpoints: {self.calculate_endpoint}, {self.row_pmis_endpoint}"
        )

    def get_pmi_scores(
        self, list_r: list[str], list_s: list[str]
    ) -> Dict[Tuple[str, str, str, str], float]:
        """
        Retrieve PMI scores for all valid quadruples from the Go service.

        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set

        Returns:
            Dictionary mapping (ri, sj, rk, sl) tuples to PMI scores.
            Only includes quadruples with positive PMI scores (co-occurrence evidence).
        """
        if not list_r or not list_s:
            raise ValueError("list_r and list_s must not be empty")

        logger.info(
            f"Requesting PMI scores from Go service: |R|={len(list_r)}, |S|={len(list_s)}"
        )

        # Prepare request payload
        payload = {"listR": list_r, "listS": list_s}

        try:
            # Make request to Go service
            response = requests.post(
                self.calculate_endpoint,
                json=payload,
                timeout=300,  # 5 minute timeout for large datasets
            )
            response.raise_for_status()

            data = response.json()

            # Log metadata if available
            if "metadata" in data:
                metadata = data["metadata"]
                logger.info(
                    f"Go service metadata: "
                    f"listR_cardinality={metadata.get('listR_cardinality', 0)}, "
                    f"listS_cardinality={metadata.get('listS_cardinality', 0)}, "
                    f"pairs_generated={metadata.get('pairs_generated', 0)}, "
                    f"table_rows_loaded={metadata.get('table_rows_loaded', 0)}"
                )

            # Log timing information if available
            if "timings" in data:
                total_duration = sum(
                    t.get("duration_seconds", 0) for t in data["timings"]
                )
                logger.info(f"Go service total duration: {total_duration:.2f}s")
                for timing in data["timings"]:
                    logger.debug(
                        f"  {timing.get('step', 'unknown')}: "
                        f"{timing.get('duration_seconds', 0):.2f}s"
                    )

            # Parse results into the format expected by CS-JP-LP
            results = data.get("results", [])
            w_ijkl_scores = {}

            for item in results:
                quad_str = item.get("quad", "")
                pmi = item.get("pmi", 0.0)

                # Parse quad string "ri,sj,rk,sl" into tuple
                parts = quad_str.split(",")
                if len(parts) != 4:
                    logger.warning(f"Invalid quad format: {quad_str}")
                    continue

                ri, sj, rk, sl = parts
                w_ijkl_scores[(ri, sj, rk, sl)] = pmi

            logger.info(
                f"Retrieved {len(w_ijkl_scores)} PMI scores from Go service "
                f"(total_found={data.get('total_found', 0)})"
            )

            return w_ijkl_scores

        except requests.exceptions.Timeout:
            logger.error(f"Request to Go service timed out after 300 seconds")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Failed to connect to Go service at {self.calculate_endpoint}: {e}"
            )
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"Go service returned error: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"Response body: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Go service failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while retrieving PMI scores: {e}")
            raise

    def get_row_pmi_scores(
        self, list_r: list[str], list_s: list[str]
    ) -> Dict[Tuple[str, str], float]:
        """
        Retrieve row-level PMI scores for pairs from the Go service.

        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set

        Returns:
            Dictionary mapping (r_i, s_j) tuples to PMI scores.
            Only includes pairs with positive PMI scores (co-occurrence evidence).
        """
        if not list_r or not list_s:
            raise ValueError("list_r and list_s must not be empty")

        logger.info(
            f"Requesting row-level PMI scores from Go service: |R|={len(list_r)}, |S|={len(list_s)}"
        )

        # Prepare request payload
        payload = {"listR": list_r, "listS": list_s}

        try:
            # Make request to Go service
            response = requests.post(
                self.row_pmis_endpoint,
                json=payload,
                timeout=300,  # 5 minute timeout for large datasets
            )
            response.raise_for_status()

            data = response.json()

            # Log metadata if available
            if "metadata" in data:
                metadata = data["metadata"]
                logger.info(
                    f"Go service metadata: "
                    f"listR_cardinality={metadata.get('listR_cardinality', 0)}, "
                    f"listS_cardinality={metadata.get('listS_cardinality', 0)}, "
                    f"total_pairs={metadata.get('total_pairs', 0)}, "
                    f"valid_pairs={metadata.get('valid_pairs', 0)}, "
                    f"zeros_filtered={metadata.get('zeros_filtered', 0)}"
                )

            # Log timing information if available
            if "timings" in data:
                total_duration = sum(
                    t.get("duration_seconds", 0) for t in data["timings"]
                )
                logger.info(f"Go service total duration: {total_duration:.2f}s")
                for timing in data["timings"]:
                    logger.debug(
                        f"  {timing.get('step', 'unknown')}: "
                        f"{timing.get('duration_seconds', 0):.2f}s"
                    )

            # Parse results
            results = data.get("results", [])
            pmi_scores = {}

            for item in results:
                r_i = item.get("r_i", "")
                s_j = item.get("s_j", "")
                pmi = item.get("pmi", 0.0)

                if r_i and s_j:
                    pmi_scores[(r_i, s_j)] = pmi
                else:
                    logger.warning(f"Invalid pair format: r_i={r_i}, s_j={s_j}")

            logger.info(
                f"Retrieved {len(pmi_scores)} row-level PMI scores from Go service"
            )

            return pmi_scores

        except requests.exceptions.Timeout:
            logger.error(f"Request to Go service timed out after 300 seconds")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Failed to connect to Go service at {self.row_pmis_endpoint}: {e}"
            )
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"Go service returned error: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"Response body: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Go service failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while retrieving row PMI scores: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check if the Go service is reachable.
        """
        try:
            # Try a simple request with minimal data to check connectivity
            response = requests.get(self.go_service_url, timeout=5)
            return True
        except Exception as e:
            logger.warning(f"Go service health check failed: {e}")
            return False
