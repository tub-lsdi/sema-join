import unittest
from unittest.mock import MagicMock
from backend.services.algorithms.cs_jp_lp import CSJPLPAlgorithm


class TestCSJPLPPaperExample3(unittest.TestCase):
    """Test CS-JP-LP algorithm with paper's Example 3 data."""

    def setUp(self):
        """Set up test fixtures."""
        # Input from paper
        self.list_r = ["Germany", "United Kingdom"]
        self.list_s = ["DE", "GB", "GE"]

        # Column-level PMI scores from paper - ISO is better
        self.pmi_iso_better = {
            ("Germany", "DE", "United Kingdom", "GB"): 0.60,
            ("Germany", "GE", "United Kingdom", "GB"): 0.05,
        }

        # Reversed scenario - FIPS is better (hypothetical)
        self.pmi_fips_better = {
            ("Germany", "DE", "United Kingdom", "GB"): 0.05,
            ("Germany", "GE", "United Kingdom", "GB"): 0.60,
        }

    def _calculate_total_score(self, mapping, column_pmi_scores):
        """Calculate total objective score: Σ w_ijkl where both pairs are matched."""
        total = 0.0
        for (ri, sj, rk, sl), w_ijkl in column_pmi_scores.items():
            if mapping.get(ri) == sj and mapping.get(rk) == sl:
                total += w_ijkl
        return total

    def test_cs_jp_lp_chooses_higher_column_score_iso(self):
        """Test that CS-JP-LP picks ISO when ISO has higher column-level score."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.pmi_iso_better

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert - Should choose ISO (DE) because column score is higher (0.60 > 0.05)
        self.assertEqual(
            result_mapping["Germany"],
            "DE",
            "Should choose DE when (Germany,DE,UK,GB) score is higher",
        )
        self.assertEqual(
            result_mapping["United Kingdom"],
            "GB",
            "UK should map to GB in ISO scenario",
        )

        # Verify that the chosen solution has the higher score
        chosen_score = self._calculate_total_score(result_mapping, self.pmi_iso_better)
        alternative_mapping = {"Germany": "GE", "United Kingdom": "GB"}
        alternative_score = self._calculate_total_score(
            alternative_mapping, self.pmi_iso_better
        )
        self.assertGreater(
            chosen_score,
            alternative_score,
            "Chosen solution should have higher score than alternative",
        )

    def test_cs_jp_lp_chooses_higher_column_score_fips(self):
        """Test that CS-JP-LP picks FIPS when FIPS has higher column-level score."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.pmi_fips_better

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert - Should choose FIPS (GE) because column score is higher (0.60 > 0.05)
        self.assertEqual(
            result_mapping["Germany"],
            "GE",
            "Should choose GE when (Germany,GE,UK,GB) score is higher",
        )
        self.assertEqual(
            result_mapping["United Kingdom"],
            "GB",
            "UK should map to GB in FIPS scenario",
        )

        # Verify that the chosen solution has the higher score
        chosen_score = self._calculate_total_score(result_mapping, self.pmi_fips_better)
        alternative_mapping = {"Germany": "DE", "United Kingdom": "GB"}
        alternative_score = self._calculate_total_score(
            alternative_mapping, self.pmi_fips_better
        )
        self.assertGreater(
            chosen_score,
            alternative_score,
            "Chosen solution should have higher score than alternative",
        )

    def test_cs_jp_lp_maximizes_objective_function(self):
        """Test that CS-JP-LP maximizes the objective function."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.pmi_iso_better

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Calculate score for all possible valid mappings
        all_possible_mappings = [
            {"Germany": "DE", "United Kingdom": "GB"},
            {"Germany": "GE", "United Kingdom": "GB"},
            {"Germany": "DE", "United Kingdom": "GE"},
            {"Germany": "GE", "United Kingdom": "GE"},
            {"Germany": "DE", "United Kingdom": "DE"},
            {"Germany": "GE", "United Kingdom": "DE"},
        ]

        chosen_score = self._calculate_total_score(result_mapping, self.pmi_iso_better)

        # Assert that chosen solution has score >= all other solutions
        for alternative_mapping in all_possible_mappings:
            alternative_score = self._calculate_total_score(
                alternative_mapping, self.pmi_iso_better
            )
            self.assertGreaterEqual(
                chosen_score,
                alternative_score,
                f"Chosen solution (score={chosen_score:.4f}) should be >= "
                f"alternative {alternative_mapping} (score={alternative_score:.4f})",
            )

    def test_cs_jp_lp_with_complex_scenario(self):
        """Test CS-JP-LP with more complex PMI scores to verify optimization."""
        # Create a scenario with 3 possible Germany codes and complex interactions
        list_r = ["Germany", "United Kingdom", "France"]
        list_s = ["DE", "GB", "FR", "GE"]

        # Complex PMI scores where optimal solution is not immediately obvious
        complex_pmi = {
            # Germany-UK pairs
            ("Germany", "DE", "United Kingdom", "GB"): 0.50,
            ("Germany", "GE", "United Kingdom", "GB"): 0.30,
            # Germany-France pairs
            ("Germany", "DE", "France", "FR"): 0.45,
            ("Germany", "GE", "France", "FR"): 0.25,
            # UK-France pairs
            ("United Kingdom", "GB", "France", "FR"): 0.40,
        }
        # Optimal solution should be: Germany→DE, UK→GB, France→FR
        # Total score: 0.50 + 0.45 + 0.40 = 1.35

        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: complex_pmi

        # Act
        result = algo.create_bridge(list_r, list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert
        chosen_score = self._calculate_total_score(result_mapping, complex_pmi)

        # Check against the expected optimal solution
        expected_optimal = {"Germany": "DE", "United Kingdom": "GB", "France": "FR"}
        optimal_score = self._calculate_total_score(expected_optimal, complex_pmi)

        self.assertAlmostEqual(
            chosen_score,
            optimal_score,
            places=4,
            msg=f"Chosen score ({chosen_score:.4f}) should equal optimal ({optimal_score:.4f})",
        )

        # Verify it's better than a suboptimal choice (Germany→GE)
        suboptimal = {"Germany": "GE", "United Kingdom": "GB", "France": "FR"}
        suboptimal_score = self._calculate_total_score(suboptimal, complex_pmi)

        self.assertGreater(
            chosen_score,
            suboptimal_score,
            f"Chosen solution ({chosen_score:.4f}) should be better than "
            f"suboptimal ({suboptimal_score:.4f})",
        )

    def test_cs_jp_lp_column_level_advantage(self):
        """
        Test that CS-JP-LP correctly uses column-level scores.

        This test verifies the key insight from the paper:
        Even though row-level scores might favor one choice (e.g., w(Germany, GE)),
        CS-JP-LP correctly considers column-level interactions and picks the
        globally optimal solution based on w(Germany, DE, UK, GB) vs w(Germany, GE, UK, GB).
        """
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.pmi_iso_better

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Calculate scores for both possible outcomes
        mapping_iso = {"Germany": "DE", "United Kingdom": "GB"}
        mapping_fips = {"Germany": "GE", "United Kingdom": "GB"}

        score_iso = self._calculate_total_score(mapping_iso, self.pmi_iso_better)
        score_fips = self._calculate_total_score(mapping_fips, self.pmi_iso_better)

        # Assert - ISO mapping should have higher column-level score
        self.assertGreater(
            score_iso,
            score_fips,
            "ISO mapping (DE+GB) should have higher column score than FIPS mixing (GE+GB)",
        )
        self.assertAlmostEqual(score_iso, 0.60, places=2)
        self.assertAlmostEqual(score_fips, 0.05, places=2)

        # Assert - Algorithm should pick the higher column-level score
        self.assertEqual(
            result_mapping,
            mapping_iso,
            "Algorithm should pick ISO mapping with higher column-level score",
        )

    def test_cs_jp_lp_all_values_mapped(self):
        """Test that all input values get mapped."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.pmi_iso_better

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert - All values from R should be present
        for r_val in self.list_r:
            self.assertIn(
                r_val, result_mapping, f"{r_val} should be in the result mapping"
            )
            self.assertIsNotNone(
                result_mapping[r_val], f"{r_val} should map to a value, not None"
            )

    def test_cs_jp_lp_many_to_one_constraint(self):
        """Test that the result satisfies many-to-one constraint."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.pmi_iso_better

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert - Each r maps to at most one s (many-to-one)
        # In this case, each r should map to exactly one s
        mapped_r_values = list(result_mapping.keys())
        self.assertEqual(
            len(mapped_r_values),
            len(set(mapped_r_values)),
            "Each r value should appear at most once",
        )

        # Each s can be mapped by multiple r's, but in this example each maps uniquely
        mapped_s_values = [s for s in result_mapping.values() if s is not None]
        self.assertGreater(len(mapped_s_values), 0, "At least one mapping should exist")


class TestCSJPLPPaperExample3Integration(unittest.TestCase):
    """Integration tests for complete CS-JP-LP workflow."""

    def test_complete_workflow(self):
        """Test complete CS-JP-LP workflow from input to output."""
        # Arrange
        list_r = ["Germany", "United Kingdom"]
        list_s = ["DE", "GB", "GE"]
        pmi_scores = {
            ("Germany", "DE", "United Kingdom", "GB"): 0.60,
            ("Germany", "GE", "United Kingdom", "GB"): 0.05,
        }

        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: pmi_scores

        # Act
        result = algo.create_bridge(list_r, list_s, top_k=10)

        # Assert - Result should be a list of dicts
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0, "Result should not be empty")

        # Assert - Each result item should have required fields
        for item in result:
            self.assertIn("r_val", item)
            self.assertIn("s_val", item)
            self.assertIn("npmi", item)
            self.assertIsInstance(item["r_val"], str)
            self.assertIsInstance(item["s_val"], str)
            self.assertIsInstance(item["npmi"], (int, float))

    def test_output_format_compatibility(self):
        """Test that output format is compatible with expected schema."""
        # Arrange
        list_r = ["Germany", "United Kingdom"]
        list_s = ["DE", "GB", "GE"]
        pmi_scores = {
            ("Germany", "DE", "United Kingdom", "GB"): 0.60,
            ("Germany", "GE", "United Kingdom", "GB"): 0.05,
        }

        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: pmi_scores

        # Act
        result = algo.create_bridge(list_r, list_s, top_k=10)

        # Assert - Can convert to mapping dict
        mapping = {r["r_val"]: r["s_val"] for r in result}
        self.assertEqual(len(mapping), 2)

        # Assert - Can extract scores
        scores = {r["r_val"]: r["npmi"] for r in result}
        self.assertEqual(len(scores), 2)
        for score in scores.values():
            self.assertGreaterEqual(score, 0.0, "Scores should be non-negative")


if __name__ == "__main__":
    unittest.main(verbosity=2)
