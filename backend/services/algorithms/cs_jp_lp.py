"""
CS-JP-LP algorithm implementation.
"""
import polars as pl
from collections import defaultdict
import pulp
from .base import BridgeAlgorithm


class CSJPLPAlgorithm(BridgeAlgorithm):
    """
    CS-JP-LP algorithm.
    
    Global optimization algorithm that considers semantic compatibility between matched pairs.
    Uses Integer Linear Programming (ILP) solver for optimal matching.
    
    Paper formulation (Equations 9-13 - CILP):
    - Algorithm 1: Round half-integral solution to CLP
    - Algorithm 2: Solve CILP
    """
    
    def create_bridge(
        self,
        list_r: list[str],
        list_s: list[str],
    ) -> list[dict]:
        """
        Create a bridge table using CS-JP-LP algorithm.
        
        This implements a two-stage approach:
        1. Solve continuous relaxation (CLP)
        2. Round to integral solution (CILP)
        
        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set
            
        Returns:
            List of dictionaries with r_val, s_val, and pmi fields
        """
        conn = self.db_connection

        # Step 1: Get all viable (r, s) pairs with positive row-level scores
        viable_pairs, row_score_dict = self._get_viable_pairs(conn, list_r, list_s)
        
        if not viable_pairs:
            return []

        # Step 2: Build column-level score lookup (w_ijkl weights)
        w_ijkl = self._build_column_scores(conn, list_r, list_s)

        # Step 3: Solve CLP (Continuous Linear Program relaxation)
        x_vars_clp, z_vars_clp = self._solve_clp(viable_pairs, list_r, w_ijkl)

        # Step 4: Algorithm 1 - Round half-integral solution
        x_tilde = self._round_solution(x_vars_clp, viable_pairs, list_r, w_ijkl)

        # Step 5: Algorithm 2 - Solve CILP (Convert to integral solution)
        x_final = self._solve_cilp(x_tilde, z_vars_clp)

        # Step 6: Extract solution and build result bridge table
        return self._extract_result(x_final, row_score_dict)

    def _get_viable_pairs(
        self,
        conn,
        list_r: list[str],
        list_s: list[str],
    ) -> tuple[list[tuple], dict]:
        """
        Get all viable (r, s) pairs with positive row-level scores.
        
        Args:
            conn: Database connection
            list_r: Normalized R values
            list_s: Normalized S values
            
        Returns:
            Tuple of (viable_pairs, row_score_dict)
        """
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

        # Build row-level score lookup (for output only)
        row_score_dict = {}
        for r_val, s_val, row_score in viable_pairs:
            row_score_dict[(r_val, s_val)] = row_score

        return viable_pairs, row_score_dict

    def _build_column_scores(
        self,
        conn,
        list_r: list[str],
        list_s: list[str],
    ) -> dict:
        """
        Build column-level score lookup (w_ijkl weights).
        
        Args:
            conn: Database connection
            list_r: Normalized R values
            list_s: Normalized S values
            
        Returns:
            Dictionary mapping pair tuples to column scores
        """
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

        return w_ijkl

    def _solve_clp(
        self,
        viable_pairs: list[tuple],
        list_r: list[str],
        w_ijkl: dict,
    ) -> tuple[dict, dict]:
        """
        Solve CLP (Continuous Linear Program relaxation).
        
        Paper Algorithm 1, Step 1: Solve CLP using standard LP.
        
        Args:
            viable_pairs: List of viable (r, s, score) tuples
            list_r: Normalized R values
            w_ijkl: Column score weights
            
        Returns:
            Tuple of (x_vars_clp, z_vars_clp)
        """
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

        return x_vars_clp, z_vars_clp

    def _round_solution(
        self,
        x_vars_clp: dict,
        viable_pairs: list[tuple],
        list_r: list[str],
        w_ijkl: dict,
    ) -> dict:
        """
        Algorithm 1 - Round half-integral solution.
        
        Paper Algorithm 1, Lines 2-11.
        
        Args:
            x_vars_clp: LP variables from CLP solution
            viable_pairs: List of viable (r, s, score) tuples
            list_r: Normalized R values
            w_ijkl: Column score weights
            
        Returns:
            Rounded solution x_tilde
        """
        # Extract optimal LP solution
        x_star = {}
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

        return x_tilde

    def _solve_cilp(
        self,
        x_tilde: dict,
        z_vars_clp: dict,
    ) -> dict:
        """
        Algorithm 2 - Solve CILP (Convert to integral solution).
        
        Paper Algorithm 2, Lines 3-9.
        
        Args:
            x_tilde: Rounded solution from Algorithm 1
            z_vars_clp: Z variables from CLP
            
        Returns:
            Final integral solution x_final
        """
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

        return x_final

    def _extract_result(
        self,
        x_final: dict,
        row_score_dict: dict,
    ) -> list[dict]:
        """
        Extract solution and build result bridge table.
        
        Args:
            x_final: Final integral solution
            row_score_dict: Dictionary mapping (r,s) pairs to PMI scores
            
        Returns:
            List of bridge table entries
        """
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

