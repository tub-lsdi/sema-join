import polars as pl
import pulp
from loguru import logger
from .base import BridgeAlgorithm


class CSJPLPAlgorithm(BridgeAlgorithm):
    """
    Uses column-level PMI scores and linear programming to find optimal join mappings.
    """

    def create_bridge(
        self,
        list_r: list[str],
        list_s: list[str],
        top_k: int = 1,
    ) -> list[dict]:
        """
        Create a bridge table using CS-JP-LP algorithm.

        1. Calculate PMI scores (from database)
        2. Formulate and solve CLP
        3. Round to half-integral solution (Algorithm 1)
        4. Convert to integral solution (Algorithm 2)
        5. Extract join function
        6. Optional greedy refinement

        Args:
            list_r: Normalized list of strings from R set
            list_s: Normalized list of strings from S set
            top_k: IGNORED in CS-JP-LP. This parameter is kept for API consistency
                   with RS-JP but has no effect. CS-JP-LP is a global optimization 
                   problem that finds ONE complete mapping with the highest aggregate 
                   column-level score. Unlike RS-JP (which independently finds top-k 
                   candidates per row), CS-JP-LP considers all rows jointly, so there 
                   is only one globally optimal solution.

        Returns:
            List of dictionaries with r_val, s_val, and npmi fields.
            Each result represents one row in the optimal global mapping.
            Note: 'npmi' field contains aggregate PMI score (sum), not a single PMI value.
        """
        conn = self.db_connection

        # Warn if top_k > 1 (parameter is ignored)
        if top_k > 1:
            logger.warning(
                f"CS-JP-LP: top_k={top_k} is ignored. CS-JP-LP always returns "
                f"ONE globally optimal mapping. Use RS-JP if you need top-k "
                f"candidates per row."
            )

        # Register inputs as temp tables
        conn.register("input_r", pl.DataFrame({"r_val": list_r}))
        conn.register("input_s", pl.DataFrame({"s_val": list_s}))

        # Step 1: Fetch column-level PMI scores from database
        w_ijkl_scores = self._fetch_pmi_scores(conn)
        print(w_ijkl_scores)

        # Step 2: Solve CILP using Algorithm 2 (which constructs CLP, calls Algorithm 1, and converts to integral)
        x_star, z_star = self._algorithm_2_solve_cilp(
            list_r, list_s, w_ijkl_scores
        )

        # Note: z_star is returned by Algorithm 2 per the paper's formal specification (which states
        # Algorithm 2 returns both x* and z*), but is not used in subsequent steps. The z* variables
        # are auxiliary variables introduced to linearize the quadratic term xij×xkl in the original
        # CIQP formulation. Once we have the integral solution x*, we only need it to extract the
        # join function J(ri) = sj where x*ij = 1. The z* values would only be needed to verify the
        # objective function value, but are not required for the actual join mapping.

        # Step 3: Extract join function
        join_mapping = self._extract_join_function(list_r, list_s, x_star)

        # Step 4: Optional greedy refinement
        join_mapping = self._greedy_refinement(
            list_r, list_s, join_mapping, w_ijkl_scores
        )

        # Convert to output format
        result = []
        for r_val, s_val in join_mapping.items():
            if s_val is not None:  # Not ⊥
                # Calculate the objective score for this mapping
                score = self._calculate_mapping_score(
                    r_val, s_val, join_mapping, w_ijkl_scores
                )
                result.append({
                    "r_val": r_val,
                    "s_val": s_val,
                    "npmi": score  # Use 'npmi' field name
                })

        return result

    def _fetch_pmi_scores(self, conn):
        """
        Fetch column-level PMI scores from database.

        Note: Assumes input_r and input_s tables have been registered in conn.
        These tables contain the r_val and s_val columns to filter on.

        The database stores PMI scores in canonicalized form to save space,
        but the algorithm needs scores for all ordered pairs (ri,sj,rk,sl) where i≠k.
        Since PMI((ri,sj),(rk,sl)) = PMI((rk,sl),(ri,sj)) (symmetric), we expand
        each stored entry into both directions.

        We assume that the direction of the join J : R → S 
        is known without loss of generality, since both join directions can be 
        tested and the one with a better score can be picked.

        Returns:
            w_ijkl_scores: dict[(ri, sj, rk, sl)] -> column PMI score
        """
        # Fetch column-level PMI scores (only positive, as stored in DB)
        # Filters based on input_r and input_s tables registered in create_bridge()
        column_pmi_query = """
            SELECT
                cp.pairA_v1,
                cp.pairA_v2,
                cp.pairB_v1,
                cp.pairB_v2,
                cp.npmi_score AS column_pmi
            FROM column_npmi_scores AS cp
            WHERE
                (cp.pairA_v1 IN (SELECT r_val FROM input_r)) AND
                (cp.pairA_v2 IN (SELECT r_val FROM input_r)) AND
                (cp.pairB_v1 IN (SELECT s_val FROM input_s)) AND
                (cp.pairB_v2 IN (SELECT s_val FROM input_s))
        """
        column_pmi_df = conn.execute(column_pmi_query).pl()

        w_ijkl_scores = {}
        for row in column_pmi_df.iter_rows(named=True):
            ri, sj, rk, sl = row["ri"], row["sj"], row["rk"], row["sl"]
            pmi_value = row["column_pmi"]

            # Store the fetched direction: wᵢⱼₖₗ = PMI((rᵢ, sⱼ), (rₖ, sₗ))
            w_ijkl_scores[(ri, sj, rk, sl)] = pmi_value

            # The database only stores canonicalized pairs, but the algorithm's
            # objective function sums over ALL ordered pairs where i≠k.
            # Since PMI((ri,sj),(rk,sl)) = PMI((rk,sl),(ri,sj)), we can reuse
            # the same PMI value for the reverse direction.
            w_ijkl_scores[(rk, sl, ri, sj)] = pmi_value

        return w_ijkl_scores

    def _solve_clp(self, list_r: list[str], list_s: list[str], w_ijkl_scores: dict):
        """
        Formulate CILP, relax to CLP, and solve.

        Returns:
            x_bar: dict[(ri, sj)] -> fractional value in [0, 1]
            z_bar: dict[(ri, sj, rk, sl)] -> fractional value in [0, 1]
        """
        # Create LP problem (minimization)
        prob = pulp.LpProblem("CLP", pulp.LpMinimize)

        # Create decision variables x̄ᵢⱼ ∈ [0, 1]
        x_vars = {}
        for ri in list_r:
            for sj in list_s:
                x_vars[(ri, sj)] = pulp.LpVariable(
                    f"x_{ri}_{sj}", lowBound=0, upBound=1, cat='Continuous'
                )

        # Create decision variables z̄ᵢⱼₖₗ ∈ [0, 1]
        z_vars = {}
        for (ri, sj, rk, sl), w_ijkl in w_ijkl_scores.items():
            if ri != rk:  # Only for i ≠ k as per guide
                z_vars[(ri, sj, rk, sl)] = pulp.LpVariable(
                    f"z_{ri}_{sj}_{rk}_{sl}", lowBound=0, upBound=1, cat='Continuous'
                )

        # Objective function: minimize Σ wᵢⱼₖₗ × (1 - z̄ᵢⱼₖₗ)
        objective = pulp.lpSum([
            w_ijkl * (1 - z_vars[(ri, sj, rk, sl)])
            for (ri, sj, rk, sl), w_ijkl in w_ijkl_scores.items()
            if (ri, sj, rk, sl) in z_vars
        ])
        prob += objective

        # Constraint 1: Σ(sj∈S) x̄ᵢⱼ ≤ 1 for all i ∈ [|R|]
        # Each ri maps to at most one sj
        for ri in list_r:
            prob += pulp.lpSum([x_vars[(ri, sj)] for sj in list_s]) <= 1

        # Constraint 2: z̄ᵢⱼₖₗ ≤ (1/2) × (x̄ᵢⱼ + x̄ₖₗ) for all i≠k
        for (ri, sj, rk, sl) in z_vars.keys():
            prob += z_vars[(ri, sj, rk, sl)] <= 0.5 * \
                (x_vars[(ri, sj)] + x_vars[(rk, sl)])

        # Solve the LP
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if prob.status != pulp.LpStatusOptimal:
            logger.warning(f"LP solver status: {pulp.LpStatus[prob.status]}")

        # Extract solution (x̄*ᵢⱼ, z̄*ᵢⱼₖₗ)
        x_bar = {}
        for (ri, sj), var in x_vars.items():
            x_bar[(ri, sj)] = var.varValue if var.varValue is not None else 0.0

        z_bar = {}
        for (ri, sj, rk, sl), var in z_vars.items():
            z_bar[(ri, sj, rk, sl)
                  ] = var.varValue if var.varValue is not None else 0.0

        return x_bar, z_bar

    def _algorithm_1_round_to_half_integral(
        self,
        list_r: list[str],
        list_s: list[str],
        w_ijkl_scores: dict
    ):
        """
        Round to Half-Integral Solution.

        Input: CLP program (via list_r, list_s, w_ijkl_scores)
        Output: Half-integral solution (x̃*ᵢⱼ, z̃*ᵢⱼₖₗ) where x̃*ᵢⱼ ∈ {0, 1} and z̃*ᵢⱼₖₗ ∈ {0, 1/2, 1}

        Returns:
            x_tilde: dict[(ri, sj)] -> value in {0, 1}
            z_tilde: dict[(ri, sj, rk, sl)] -> value in {0, 1/2, 1}
        """
        # Step 1: Solve CLP to obtain optimal solution
        x_bar, z_bar = self._solve_clp(list_r, list_s, w_ijkl_scores)

        # Step 2: Round x variables to integral values
        x_tilde = {}
        for ri in list_r:
            # Check if x̄*ᵢⱼ is already integral for all j
            x_values_for_ri = {sj: x_bar.get((ri, sj), 0.0) for sj in list_s}
            all_integral = all(
                abs(val - round(val)) < 1e-9
                for val in x_values_for_ri.values()
            )

            if all_integral:
                # Already integral, keep as is
                for sj in list_s:
                    x_tilde[(ri, sj)] = round(x_bar.get((ri, sj), 0.0))
            else:
                # Contains fractional values, need to round
                # Calculate contribution scores: cᵢⱼ = Σ(rₖ∈R, k≠i) Σ(sₗ∈S) (1/2) × wᵢⱼₖₗ
                contribution_scores = {}
                for sj in list_s:
                    c_ij = 0.0
                    for rk in list_r:
                        if rk != ri:  # k ≠ i
                            for sl in list_s:
                                w_ijkl = w_ijkl_scores.get(
                                    (ri, sj, rk, sl), 0.0)
                                c_ij += 0.5 * w_ijkl
                    contribution_scores[sj] = c_ij

                # Pick the best candidate: p = argmaxⱼ cᵢⱼ
                if contribution_scores:
                    p = max(contribution_scores.items(), key=lambda x: x[1])[0]
                    # Round: x̃*ᵢₚ ← 1, x̃*ᵢⱼ ← 0 for all j ≠ p
                    for sj in list_s:
                        x_tilde[(ri, sj)] = 1 if sj == p else 0
                else:
                    # No contribution scores, set all to 0
                    for sj in list_s:
                        x_tilde[(ri, sj)] = 0

        # Step 3: Calculate z̃*ᵢⱼₖₗ from x̃*ᵢⱼ
        # z̃*ᵢⱼₖₗ = (1/2) × (x̃*ᵢⱼ + x̃*ₖₗ) for all i, k ∈ [|R|], j, l ∈ [|S|], k ≠ i
        z_tilde = {}
        for ri in list_r:
            for sj in list_s:
                for rk in list_r:
                    if rk != ri:  # k ≠ i
                        for sl in list_s:
                            z_tilde[(ri, sj, rk, sl)] = 0.5 * (
                                x_tilde.get((ri, sj), 0) +
                                x_tilde.get((rk, sl), 0)
                            )

        # Step 4: Return half-integral solution
        return x_tilde, z_tilde

    def _algorithm_2_solve_cilp(self, list_r: list[str], list_s: list[str],
                                w_ijkl_scores: dict):
        """
        Solve CILP.

        Input: CILP program (via list_r, list_s, w_ijkl_scores)
        Output: Integral solution (x*ᵢⱼ, z*ᵢⱼₖₗ) where both are in {0, 1}

        Returns:
            x_star: dict[(ri, sj)] -> value in {0, 1}
            z_star: dict[(ri, sj, rk, sl)] -> value in {0, 1}
        """
        # Step 1: Construct CLP from CILP (relaxation - same formulation, just [0,1] instead of {0,1})
        # (This is implicit - the CLP is defined by list_r, list_s, w_ijkl_scores)

        # Step 2: Obtain half-integral solution using Algorithm 1
        # Algorithm 1 will solve the CLP and round to half-integral
        x_tilde, z_tilde = self._algorithm_1_round_to_half_integral(
            list_r, list_s, w_ijkl_scores
        )

        # Step 3: Set x*ᵢⱼ ← x̃*ᵢⱼ (already integral from Algorithm 1)
        x_star = x_tilde.copy()

        # Step 4: Calculate z*ᵢⱼₖₗ from x*ᵢⱼ
        z_star = {}
        for ri in list_r:
            for sj in list_s:
                for rk in list_r:
                    if rk != ri:  # k ≠ i
                        for sl in list_s:
                            # If x*ᵢⱼ = 1 AND x*ₖₗ = 1: z*ᵢⱼₖₗ ← 1, else 0
                            if x_star.get((ri, sj), 0) == 1 and x_star.get((rk, sl), 0) == 1:
                                z_star[(ri, sj, rk, sl)] = 1
                            else:
                                z_star[(ri, sj, rk, sl)] = 0

        # Step 5: Return integral solution
        return x_star, z_star

    def _extract_join_function(
        self,
        list_r: list[str],
        list_s: list[str],
        x_star: dict
    ):
        """
        Extract the Join Function.

        Returns:
            join_mapping: dict[ri] -> sj or None (for ⊥)
        """
        join_mapping = {}

        for ri in list_r:
            mapped_sj = None
            for sj in list_s:
                if x_star.get((ri, sj), 0) == 1:
                    mapped_sj = sj
                    break
            join_mapping[ri] = mapped_sj  # None represents ⊥

        return join_mapping

    def _greedy_refinement(
        self,
        list_r: list[str],
        list_s: list[str],
        join_mapping: dict,
        w_ijkl_scores: dict
    ):
        """
        Optional Greedy Refinement.

        Returns:
            improved_mapping: dict[ri] -> sj or None
        """
        improved = True
        current_mapping = join_mapping.copy()

        while improved:
            improved = False
            current_score = self._calculate_total_objective(
                current_mapping, w_ijkl_scores)

            for ri in list_r:
                best_sj = current_mapping[ri]
                best_score = current_score

                # Try each possible sj (including None for ⊥)
                candidates = list_s + [None]
                for sj in candidates:
                    if sj == current_mapping[ri]:
                        continue  # Skip current assignment

                    # Try this assignment
                    test_mapping = current_mapping.copy()
                    test_mapping[ri] = sj
                    test_score = self._calculate_total_objective(
                        test_mapping, w_ijkl_scores)

                    if test_score > best_score:
                        best_score = test_score
                        best_sj = sj

                # If we found a better assignment, update it
                if best_sj != current_mapping[ri]:
                    current_mapping[ri] = best_sj
                    current_score = best_score
                    improved = True

        return current_mapping

    def _calculate_total_objective(self, join_mapping: dict, w_ijkl_scores: dict):
        """
        Calculate the total objective score for a join mapping.
        """
        total_score = 0.0

        for (ri, sj, rk, sl), w_ijkl in w_ijkl_scores.items():
            # Check if both mappings exist
            if join_mapping.get(ri) == sj and join_mapping.get(rk) == sl:
                total_score += w_ijkl

        return total_score

    def _calculate_mapping_score(
        self,
        r_val: str,
        s_val: str,
        join_mapping: dict,
        w_ijkl_scores: dict
    ):
        """
        Calculate the contribution score for a specific (r_val, s_val) mapping.

        Returns the sum of column-level PMI scores

        Note: This is an aggregate score (sum of multiple PMI values), not bounded.
        Values can be large as they represent cumulative evidence for this mapping
        across all column-level co-occurrences.
        """
        score = 0.0

        for (ri, sj, rk, sl), w_ijkl in w_ijkl_scores.items():
            # Count if this mapping is part of a matched pair
            if (ri == r_val and sj == s_val and
                    join_mapping.get(rk) == sl):
                score += w_ijkl
            elif (rk == r_val and sl == s_val and
                  join_mapping.get(ri) == sj):
                score += w_ijkl

        return score
