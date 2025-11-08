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

        # Column-level PMI scores from paper
        self.paper_column_pmi = {
            ("Germany", "DE", "United Kingdom", "GB"): 0.60,
            ("Germany", "GE", "United Kingdom", "GB"): 0.05,
        }

        # Expected results from paper
        self.expected_mapping = {
            "Germany": "DE",
            "United Kingdom": "GB"
        }
        self.expected_score = 0.60

    def _calculate_total_score(self, mapping, column_pmi_scores):
        """Calculate total objective score: Σ w_ijkl where both pairs are matched."""
        total = 0.0
        for (ri, sj, rk, sl), w_ijkl in column_pmi_scores.items():
            if mapping.get(ri) == sj and mapping.get(rk) == sl:
                total += w_ijkl
        return total

    def test_cs_jp_lp_output_mapping(self):
        """Test that CS-JP-LP produces correct join mapping."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.paper_column_pmi

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert
        self.assertEqual(result_mapping["Germany"], "DE",
                         "Germany should map to DE (ISO standard)")
        self.assertEqual(result_mapping["United Kingdom"], "GB",
                         "United Kingdom should map to GB")
        self.assertEqual(result_mapping, self.expected_mapping,
                         "Complete mapping should match paper's expected output")

    def test_cs_jp_lp_objective_score(self):
        """Test that CS-JP-LP produces correct objective score."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.paper_column_pmi

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}
        total_score = self._calculate_total_score(
            result_mapping, self.paper_column_pmi)

        # Assert
        self.assertAlmostEqual(total_score, self.expected_score, places=4,
                               msg="Total objective score should be 0.6000")

    def test_cs_jp_lp_semantic_consistency(self):
        """Test that CS-JP-LP ensures semantic consistency (both ISO standard)."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.paper_column_pmi

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert - Germany should use ISO (DE) not FIPS (GE)
        self.assertEqual(result_mapping["Germany"], "DE",
                         "Germany should use ISO code (DE), not FIPS code (GE)")

        # Assert - This ensures consistency: both Germany and UK use ISO standard
        # DE is ISO for Germany, GB is ISO for UK
        # If Germany mapped to GE (FIPS), it would be inconsistent with GB (ISO)
        self.assertNotEqual(result_mapping["Germany"], "GE",
                            "Germany should NOT use FIPS code (GE) which would be inconsistent")

    def test_cs_jp_lp_column_level_advantage(self):
        """
        Test that CS-JP-LP correctly uses column-level scores.

        This test verifies the key insight from the paper:
        Even though row-level w(Germany, GE) = 0.80 > w(Germany, DE) = 0.79,
        CS-JP-LP correctly picks Germany→DE because the column-level score
        w(Germany, DE, UK, GB) = 0.60 >> w(Germany, GE, UK, GB) = 0.05
        """
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.paper_column_pmi

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Calculate scores for both possible outcomes
        mapping_iso = {"Germany": "DE", "United Kingdom": "GB"}
        mapping_fips = {"Germany": "GE", "United Kingdom": "GB"}

        score_iso = self._calculate_total_score(
            mapping_iso, self.paper_column_pmi)
        score_fips = self._calculate_total_score(
            mapping_fips, self.paper_column_pmi)

        # Assert - ISO mapping should have higher column-level score
        self.assertGreater(score_iso, score_fips,
                           "ISO mapping (DE+GB) should have higher column score than FIPS mixing (GE+GB)")
        self.assertAlmostEqual(score_iso, 0.60, places=2)
        self.assertAlmostEqual(score_fips, 0.05, places=2)

        # Assert - Algorithm should pick the higher column-level score
        self.assertEqual(result_mapping, mapping_iso,
                         "Algorithm should pick ISO mapping with higher column-level score")

    def test_cs_jp_lp_all_values_mapped(self):
        """Test that all input values get mapped."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.paper_column_pmi

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert - All values from R should be present
        for r_val in self.list_r:
            self.assertIn(r_val, result_mapping,
                          f"{r_val} should be in the result mapping")
            self.assertIsNotNone(result_mapping[r_val],
                                 f"{r_val} should map to a value, not None")

    def test_cs_jp_lp_many_to_one_constraint(self):
        """Test that the result satisfies many-to-one constraint."""
        # Arrange
        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: self.paper_column_pmi

        # Act
        result = algo.create_bridge(self.list_r, self.list_s, top_k=10)
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Assert - Each r maps to at most one s (many-to-one)
        # In this case, each r should map to exactly one s
        mapped_r_values = list(result_mapping.keys())
        self.assertEqual(len(mapped_r_values), len(set(mapped_r_values)),
                         "Each r value should appear at most once")

        # Each s can be mapped by multiple r's, but in this example each maps uniquely
        mapped_s_values = [s for s in result_mapping.values() if s is not None]
        self.assertGreater(len(mapped_s_values), 0,
                           "At least one mapping should exist")


class TestCSJPLPPaperExample3Integration(unittest.TestCase):
    """Integration tests for complete CS-JP-LP workflow."""

    def test_complete_workflow(self):
        """Test complete CS-JP-LP workflow from input to output."""
        # Arrange
        list_r = ["Germany", "United Kingdom"]
        list_s = ["DE", "GB", "GE"]
        paper_column_pmi = {
            ("Germany", "DE", "United Kingdom", "GB"): 0.60,
            ("Germany", "GE", "United Kingdom", "GB"): 0.05,
        }

        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: paper_column_pmi

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
        paper_column_pmi = {
            ("Germany", "DE", "United Kingdom", "GB"): 0.60,
            ("Germany", "GE", "United Kingdom", "GB"): 0.05,
        }

        mock_conn = MagicMock()
        algo = CSJPLPAlgorithm(mock_conn)
        algo._fetch_pmi_scores = lambda conn: paper_column_pmi

        # Act
        result = algo.create_bridge(list_r, list_s, top_k=10)

        # Assert - Can convert to mapping dict
        mapping = {r["r_val"]: r["s_val"] for r in result}
        self.assertEqual(len(mapping), 2)

        # Assert - Can extract scores
        scores = {r["r_val"]: r["npmi"] for r in result}
        self.assertEqual(len(scores), 2)
        for score in scores.values():
            self.assertGreaterEqual(score, 0.0,
                                    "Scores should be non-negative")


if __name__ == "__main__":
    unittest.main(verbosity=2)

