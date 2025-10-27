"""
Semantic Join Service class with integrated RS-JP and CS-JP-LP join algorithms.
"""
import duckdb
import polars as pl
from typing import Literal
from collections import defaultdict
import pulp
from backend.services.CorpusService import NormalizationStrategy

# Type alias for join methods
JoinMethod = Literal["row", "column"]


class SemanticJoinService:
    """
    Service class that implements semantic join functionality.

    This class provides two join algorithms from the SEMA-JOIN paper:
    - RS-JP (Row-based Semantic Join Processing): Greedy algorithm using row-level PMI scores
    - CS-JP-LP (Column-based with Linear Programming): Optimal global matching using ILP solver
    """

    def __init__(self, db_connection: duckdb.DuckDBPyConnection):
        """
        Initialize the semantic join service.

        Args:
            db_connection: Database connection (created in main.py)
        """
        self.db_connection = db_connection
        # Use the same normalization strategy as corpus ingestion
        self.normalizer = NormalizationStrategy.ALPHANUMERIC_STRICT

    def _normalize(self, value: str) -> str:
        """
        Normalize a value using the same strategy as corpus ingestion.

        Args:
            value: Raw value to normalize

        Returns:
            Normalized value
        """
        return self.normalizer.normalize(value)

    def _get_pmi_score(self, v1: str, v2: str, con: duckdb.DuckDBPyConnection) -> float:
        """
        Private helper to lookup a precomputed PMI score.

        Args:
            v1: First value
            v2: Second value
            con: Database connection

        Returns:
            PMI score or negative infinity if not found
        """
        q = con.execute(
            """
            SELECT pmi FROM pmi_scores
            WHERE v1 = ? AND v2 = ?
            """,
            (min(v1, v2), max(v1, v2)),
        )
        row = q.fetchone()
        return row[0] if row else float("-inf")

    def create_bridge_table(
        self,
        list_r: list[str],
        list_s: list[str],
        join_method: JoinMethod = "row",
    ) -> list[dict]:
        """
        Create a bridge table using the specified join algorithm.

        Args:
            list_r: First list of strings (R set - to be matched)
            list_s: Second list of strings (S set - candidates)
            join_method: "row" for RS-JP (row-based) or "column" for CS-JP (column-based)

        Returns:
            List of dictionaries with r_val, s_val, and pmi/score fields

        Raises:
            ValueError: If either list is empty or join_method is invalid
        """
        # Validation
        if not list_r:
            raise ValueError("list_r cannot be empty")
        if not list_s:
            raise ValueError("list_s cannot be empty")
        if join_method not in ["row", "column"]:
            raise ValueError(
                f"join_method must be 'row' or 'column', got '{join_method}'")

        # Normalize input values to match database normalization
        normalized_r = [self._normalize(v) for v in list_r]
        normalized_s = [self._normalize(v) for v in list_s]

        # Route to appropriate algorithm
        if join_method == "row":
            return self._create_bridge_rs_jp(normalized_r, normalized_s)
        else:  # join_method == "column"
            # CS-JP-LP with ILP solver
            return self._create_bridge_cs_jp(normalized_r, normalized_s)

    def _create_bridge_rs_jp(
        self,
        list_r: list[str],
        list_s: list[str],
    ) -> list[dict]:
        """
        RS-JP (Row-based Semantic Join Processing) algorithm.

        Greedy algorithm: Each r independently picks its best s based on row-level PMI.
        """
        conn = self.db_connection

        # Use Polars to efficiently register inputs as temp tables
        conn.register("input_r", pl.DataFrame({"r_val": list_r}))
        conn.register("input_s", pl.DataFrame({"s_val": list_s}))

        # Query to get only the highest PMI candidate for each r_val
        bridge_query = """
            WITH all_candidates AS (
                SELECT
                    r.r_val,
                    s.s_val,
                    pmi.pmi,
                    ROW_NUMBER() OVER (PARTITION BY r.r_val ORDER BY pmi.pmi DESC) as rn
                FROM input_r AS r
                JOIN pmi_scores AS pmi
                    ON r.r_val = pmi.v1 OR r.r_val = pmi.v2
                JOIN input_s AS s
                    ON (s.s_val = pmi.v1 OR s.s_val = pmi.v2)
                WHERE
                    ((r.r_val = pmi.v1 AND s.s_val = pmi.v2) OR
                     (r.r_val = pmi.v2 AND s.s_val = pmi.v1))
                    AND pmi.pmi > 0
            )
            SELECT
                r_val,
                s_val,
                pmi
            FROM all_candidates
            WHERE rn = 1
            ORDER BY r_val
        """
        bridge_df = conn.execute(bridge_query).pl()
        return bridge_df.to_dicts()

    def _create_bridge_cs_jp(
        self,
        list_r: list[str],
        list_s: list[str],
    ) -> list[dict]:
        """
        CS-JP-LP (Column-based Semantic Join Processing with Linear Programming).

        - Algorithm 1: Round half-integral solution to CLP
        - Algorithm 2: Solve CILP

        Paper formulation (Equations 9-13 - CILP):
        min Σ w_ijkl * (1 - z_ijkl)
        s.t. Σ x_ij ≤ 1, ∀i
             z_ijkl ≤ 1/2 * (x_ij + x_kl), ∀i,k ∈ R (i≠k), ∀j,l ∈ S
             x_ij, x_kl ∈ {0,1}
             z_ijkl ∈ {0,1}
        """
        conn = self.db_connection

        # Step 1: Get all viable (r, s) pairs with positive row-level scores
        conn.register("input_r", pl.DataFrame({"r_val": list_r}))
        conn.register("input_s", pl.DataFrame({"s_val": list_s}))

        row_pairs_query = """
            SELECT DISTINCT
                r.r_val,
                s.s_val,
                pmi.pmi as row_score
            FROM input_r AS r
            JOIN pmi_scores AS pmi
                ON r.r_val = pmi.v1 OR r.r_val = pmi.v2
            JOIN input_s AS s
                ON (s.s_val = pmi.v1 OR s.s_val = pmi.v2)
            WHERE
                ((r.r_val = pmi.v1 AND s.s_val = pmi.v2) OR
                 (r.r_val = pmi.v2 AND s.s_val = pmi.v1))
                AND pmi.pmi > 0
            ORDER BY pmi.pmi DESC
        """
        viable_pairs = conn.execute(row_pairs_query).fetchall()

        if not viable_pairs:
            return []

        # Step 2: Build row-level score lookup (for output only)
        row_score_dict = {}
        for r_val, s_val, row_score in viable_pairs:
            row_score_dict[(r_val, s_val)] = row_score

        # Step 3: Build column-level score lookup (w_ijkl weights)
        r_values_str = "','".join(list_r)
        s_values_str = "','".join(list_s)

        col_scores_query = f"""
            SELECT v1, v2, v3, v4, score
            FROM column_scores
            WHERE (v1 IN ('{r_values_str}') OR v2 IN ('{r_values_str}') 
                   OR v3 IN ('{r_values_str}') OR v4 IN ('{r_values_str}'))
              AND (v1 IN ('{s_values_str}') OR v2 IN ('{s_values_str}')
                   OR v3 IN ('{s_values_str}') OR v4 IN ('{s_values_str}'))
        """
        col_scores = conn.execute(col_scores_query).fetchall()

        # Build column score lookup w_ijkl for pairs of matches
        w_ijkl = defaultdict(lambda: 0.0)
        for v1, v2, v3, v4, score in col_scores:
            # Store all permutations for easy lookup
            for perm in [
                ((v1, v2), (v3, v4)),
                ((v1, v2), (v4, v3)),
                ((v2, v1), (v3, v4)),
                ((v2, v1), (v4, v3)),
                ((v3, v4), (v1, v2)),
                ((v3, v4), (v2, v1)),
                ((v4, v3), (v1, v2)),
                ((v4, v3), (v2, v1)),
            ]:
                w_ijkl[perm] = max(w_ijkl[perm], score)

        # Step 4: Solve CLP (Continuous Linear Program relaxation)
        # Paper Algorithm 1, Step 1: Solve CLP using standard LP
        prob_clp = pulp.LpProblem("CLP", pulp.LpMinimize)

        # Create continuous variables x_ij ∈ [0,1] for LP relaxation
        x_vars_clp = {}
        for r_val, s_val, _ in viable_pairs:
            var_name = f"x_{r_val}_{s_val}"
            x_vars_clp[(r_val, s_val)] = pulp.LpVariable(
                var_name, lowBound=0, upBound=1, cat='Continuous')

        # Create continuous variables z_ijkl ∈ [0,1] for LP relaxation
        z_vars_clp = {}
        r_pairs = [(r1, s1) for r1, s1, _ in viable_pairs]
        for i, (r_i, s_i) in enumerate(r_pairs):
            for j, (r_j, s_j) in enumerate(r_pairs):
                if r_i != r_j:  # Different r values (i ≠ k in paper notation)
                    var_name = f"z_{r_i}_{s_i}_{r_j}_{s_j}"
                    z_vars_clp[(r_i, s_i, r_j, s_j)] = pulp.LpVariable(
                        var_name, lowBound=0, upBound=1, cat='Continuous')

        # Objective function: min Σ w_ijkl * (1 - z_ijkl)
        objective_clp = []
        for (r_i, s_i, r_j, s_j), z_var in z_vars_clp.items():
            weight = w_ijkl.get(((r_i, s_i), (r_j, s_j)), 0.0)
            if weight > 0:
                # w_ijkl * (1 - z_ijkl) = w_ijkl - w_ijkl * z_ijkl
                objective_clp.append(weight * (1 - z_var))

        prob_clp += pulp.lpSum(objective_clp), "Total_Cost"

        # Constraint: Σ x_ij ≤ 1, ∀i (each r_i matches to at most one s_j)
        for r_val in list_r:
            matching_vars = [x_vars_clp[(r, s)]
                             for r, s, _ in viable_pairs if r == r_val]
            if matching_vars:
                prob_clp += pulp.lpSum(
                    matching_vars) <= 1, f"r_constraint_{r_val}"

        # Constraint: z_ijkl ≤ 1/2 * (x_ij + x_kl), ∀i,k ∈ R (i≠k), ∀j,l ∈ S
        for (r_i, s_i, r_j, s_j), z_var in z_vars_clp.items():
            x_ij = x_vars_clp.get((r_i, s_i))
            x_kl = x_vars_clp.get((r_j, s_j))
            if x_ij is not None and x_kl is not None:
                prob_clp += z_var <= 0.5 * \
                    (x_ij + x_kl), f"z_constraint_{r_i}_{s_i}_{r_j}_{s_j}"

        # Solve CLP
        prob_clp.solve(pulp.PULP_CBC_CMD(msg=0))

        if prob_clp.status != pulp.LpStatusOptimal:
            raise RuntimeError(
                f"CS-JP-LP: CLP solver failed with status: {pulp.LpStatus[prob_clp.status]}")

        # Step 5: Algorithm 1 - Round half-integral solution
        # Paper Algorithm 1, Lines 2-11
        x_star = {}  # Optimal LP solution
        for key, var in x_vars_clp.items():
            x_star[key] = pulp.value(var)

        x_tilde = {}  # Half-integral solution after rounding

        # For each r_i (Line 2)
        for r_val in list_r:
            r_pairs_for_i = [(r, s) for r, s, _ in viable_pairs if r == r_val]

            if not r_pairs_for_i:
                continue

            # Check if all x*_ij are already integral (Line 3)
            all_integral = all(
                x_star.get((r, s), 0) in [0.0, 1.0]
                for r, s in r_pairs_for_i
            )

            if all_integral:
                # Line 4: Keep integral values
                for r, s in r_pairs_for_i:
                    x_tilde[(r, s)] = x_star.get((r, s), 0)
            else:
                # Lines 5-9: Round fractional solution
                # Line 6: Compute c_ij = Σ_{r_k ∈ R, k≠i, s_l ∈ S} 1/2 * w_ijkl
                c_ij = {}
                for r, s in r_pairs_for_i:
                    total = 0.0
                    # Sum over all other r_k and all s_l
                    for r_k, s_l, _ in viable_pairs:
                        if r_k != r:  # k ≠ i
                            weight = w_ijkl.get(((r, s), (r_k, s_l)), 0.0)
                            total += 0.5 * weight
                    c_ij[s] = total

                # Line 7: p = argmax_j c_ij
                if c_ij:
                    p = max(c_ij, key=c_ij.get)
                    # Line 8: x̃*_ip ← 1
                    x_tilde[(r_val, p)] = 1.0
                    # Line 9: x̃*_ij ← 0, ∀j ≠ p
                    for r, s in r_pairs_for_i:
                        if s != p:
                            x_tilde[(r, s)] = 0.0
                else:
                    # No weights, set all to 0
                    for r, s in r_pairs_for_i:
                        x_tilde[(r, s)] = 0.0

        # Lines 10-11: Compute z̃*_ijkl = 1/2 * (x̃*_ij + x̃*_kl)
        z_tilde = {}
        for r_i, s_i, r_j, s_j in z_vars_clp.keys():
            x_ij = x_tilde.get((r_i, s_i), 0.0)
            x_kl = x_tilde.get((r_j, s_j), 0.0)
            z_tilde[(r_i, s_i, r_j, s_j)] = 0.5 * (x_ij + x_kl)

        # Step 6: Algorithm 2 - Solve CILP (Convert to integral solution)
        # Paper Algorithm 2, Lines 3-9
        x_final = {}
        z_final = {}

        # Lines 3-4: Copy x̃* to x*
        for key, value in x_tilde.items():
            x_final[key] = value

        # Lines 5-9: Compute z*_ijkl
        for r_i, s_i, r_j, s_j in z_vars_clp.keys():
            x_ij = x_final.get((r_i, s_i), 0.0)
            x_kl = x_final.get((r_j, s_j), 0.0)

            # Line 6-7: if x*_ij = 1 and x*_kl = 1 then z*_ijkl ← 1
            if x_ij == 1.0 and x_kl == 1.0:
                z_final[(r_i, s_i, r_j, s_j)] = 1.0
            else:
                # Line 8-9: else z*_ijkl ← 0
                z_final[(r_i, s_i, r_j, s_j)] = 0.0

        # Step 7: Extract solution and build result bridge table
        result = []
        for (r_val, s_val), x_val in x_final.items():
            if x_val == 1.0:
                row_score = row_score_dict.get((r_val, s_val), 0.0)
                result.append({
                    "r_val": r_val,
                    "s_val": s_val,
                    "pmi": row_score
                })

        return result

    def perform_join_from_bridge(
        self,
        list_r: list[dict],
        r_join_col: str,
        bridge_table: list[dict],
        list_s: list[dict],
        s_join_col: str,
    ) -> list[dict]:
        """
        Perform a three-way join using a pre-computed bridge table.

        This performs: list_r JOIN bridge_table ON r_join_col = r_val
                              JOIN list_s ON s_val = s_join_col

        Args:
            list_r: List of records from R dataset
            r_join_col: Column name in list_r to join with bridge_table.r_val
            bridge_table: Bridge table with r_val, s_val, pmi
            list_s: List of records from S dataset
            s_join_col: Column name in list_s to join with bridge_table.s_val

        Returns:
            List of joined records containing all columns from R, bridge, and S

        Raises:
            ValueError: If inputs are invalid or join columns don't exist
        """
        # Validation
        if not list_r:
            raise ValueError("list_r cannot be empty")
        if not list_s:
            raise ValueError("list_s cannot be empty")
        if not bridge_table:
            raise ValueError("bridge_table cannot be empty")

        # Check if join columns exist
        if r_join_col not in list_r[0]:
            raise ValueError(f"Column '{r_join_col}' not found in list_r")
        if s_join_col not in list_s[0]:
            raise ValueError(f"Column '{s_join_col}' not found in list_s")

        # Use the database connection from main.py
        conn = self.db_connection

        # Register inputs as temp tables using Polars
        conn.register("temp_r", pl.DataFrame(list_r))
        conn.register("temp_bridge", pl.DataFrame(bridge_table))
        conn.register("temp_s", pl.DataFrame(list_s))

        # Perform three-way join with normalization
        # Bridge table has normalized values
        # Normalization: strip -> lowercase -> replace non-alphanumeric -> trim
        join_query = f"""
            SELECT 
                r.*,
                bridge.r_val,
                bridge.s_val,
                bridge.pmi,
                s.*
            FROM temp_r AS r
            INNER JOIN temp_bridge AS bridge
                ON TRIM(REGEXP_REPLACE(LOWER(TRIM(CAST(r.{r_join_col} AS VARCHAR))), '[^a-z0-9]+', ' ', 'g')) = bridge.r_val
            INNER JOIN temp_s AS s
                ON TRIM(REGEXP_REPLACE(LOWER(TRIM(CAST(s.{s_join_col} AS VARCHAR))), '[^a-z0-9]+', ' ', 'g')) = bridge.s_val
            ORDER BY r.{r_join_col}
        """

        result_df = conn.execute(join_query).pl()

        # Clean up temp tables
        conn.unregister("temp_r")
        conn.unregister("temp_bridge")
        conn.unregister("temp_s")

        return result_df.to_dicts()

    def validate_inputs(self, list_r: list[str], list_s: list[str]) -> tuple[bool, str]:
        """
        Validate input lists for the semantic join operation.

        Args:
            list_r: First list of strings
            list_s: Second list of strings

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not list_r:
            return False, "list_r cannot be empty"
        if not list_s:
            return False, "list_s cannot be empty"
        if not all(isinstance(x, str) for x in list_r):
            return False, "All elements in list_r must be strings"
        if not all(isinstance(x, str) for x in list_s):
            return False, "All elements in list_s must be strings"

        return True, ""
