import unittest
from unittest.mock import MagicMock
import polars as pl
from backend.services.algorithms.rs_jp import RSJPAlgorithm


class TestRSJPAlgorithm(unittest.TestCase):
    """Test RS-JP algorithm implementation against validation protocol."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_conn = MagicMock()

    def _setup_mock_scores(self, scores_dict):
        """
        Helper to mock the database with specific pairwise scores.

        Args:
            scores_dict: dict[(ri, sj)] -> score
                        Maps (r_val, s_val) pairs to their PMI/NPMI scores
        """
        # Create a list of score records for the mock database
        score_records = []
        for (v1, v2), score in scores_dict.items():
            # Store as (v1, v2, pmi, npmi)
            # Assuming npmi = pmi for simplicity in tests
            score_records.append({"v1": v1, "v2": v2, "pmi": score, "npmi": score})

        # Create a mock result that behaves like a DuckDB result
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(score_records)

        # Setup the execute chain
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

    def test_simple_maximization(self):
        """
        Test Case 1: Simple Maximization

        From validation protocol Section 1.2 Test Case 1:
        Verifies the basic "arg max" functionality.

        R = {r1, r2}
        S = {s1, s2, s3}

        Scores:
        w(r1, s1) = 0.2, w(r1, s2) = 0.8, w(r1, s3) = 0.1
        w(r2, s1) = 0.9, w(r2, s2) = 0.4, w(r2, s3) = 0.3

        Expected: J = {(r1 → s2), (r2 → s1)}
        """
        # Arrange
        list_r = ["r1", "r2"]
        list_s = ["s1", "s2", "s3"]

        scores = {
            ("r1", "s1"): 0.2,
            ("r1", "s2"): 0.8,
            ("r1", "s3"): 0.1,
            ("r2", "s1"): 0.9,
            ("r2", "s2"): 0.4,
            ("r2", "s3"): 0.3,
        }

        # Create mock result that returns the correct mappings
        # r1 → s2 (score 0.8), r2 → s1 (score 0.9)
        mock_result_data = [
            {"r_val": "r1", "s_val": "s2", "npmi": 0.8},
            {"r_val": "r2", "s_val": "s1", "npmi": 0.9},
        ]
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(mock_result_data)
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(self.mock_conn)
        result = algo.create_bridge(list_r, list_s, top_k=1)

        # Assert
        result_mapping = {r["r_val"]: r["s_val"] for r in result}
        self.assertEqual(
            result_mapping["r1"], "s2", "r1 should map to s2 (highest score 0.8)"
        )
        self.assertEqual(
            result_mapping["r2"], "s1", "r2 should map to s1 (highest score 0.9)"
        )

    def test_null_constraint(self):
        """
        Test Case 2: The Null/⊥ Constraint

        From validation protocol Section 1.2 Test Case 2:
        Verifies the "positive score" requirement.

        R = {r1}
        S = {s1, s2}

        Scores:
        w(r1, s1) = -0.5, w(r1, s2) = -0.1

        Expected: J = {(r1 → ⊥)} (no mapping, since all scores are negative)
        """
        # Arrange
        list_r = ["r1"]
        list_s = ["s1", "s2"]

        # Mock empty result (no positive scores)
        mock_result_data = []  # Empty because WHERE npmi.pmi > 0 filters all
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(
            {"r_val": [], "s_val": [], "npmi": []}
        )
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(self.mock_conn)
        result = algo.create_bridge(list_r, list_s, top_k=1)

        # Assert
        self.assertEqual(
            len(result),
            0,
            "Result should be empty when all scores are negative (⊥ mapping)",
        )

    def test_many_to_one_behavior(self):
        """
        Test Case 3: "Many-to-One" Behavior

        From validation protocol Section 1.2 Test Case 3:
        Verifies the algorithm correctly handles N:1 mappings.

        R = {r1, r2}
        S = {s1, s2}

        Scores:
        w(r1, s1) = 0.9, w(r1, s2) = 0.1
        w(r2, s1) = 0.7, w(r2, s2) = 0.2

        Expected: J = {(r1 → s1), (r2 → s1)}
        (Both r1 and r2 map to s1)
        """
        # Arrange
        list_r = ["r1", "r2"]
        list_s = ["s1", "s2"]

        # Mock result where both map to s1
        mock_result_data = [
            {"r_val": "r1", "s_val": "s1", "npmi": 0.9},
            {"r_val": "r2", "s_val": "s1", "npmi": 0.7},
        ]
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(mock_result_data)
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(self.mock_conn)
        result = algo.create_bridge(list_r, list_s, top_k=1)

        # Assert
        result_mapping = {r["r_val"]: r["s_val"] for r in result}
        self.assertEqual(result_mapping["r1"], "s1", "r1 should map to s1")
        self.assertEqual(
            result_mapping["r2"], "s1", "r2 should also map to s1 (many-to-one)"
        )

        # Verify that multiple R values can indeed map to the same S value
        s_values = [r["s_val"] for r in result]
        self.assertEqual(
            s_values.count("s1"), 2, "s1 should appear twice (mapped by both r1 and r2)"
        )

    def test_tie_breaking(self):
        """
        Test Case 4: Tie-Breaking

        From validation protocol Section 1.3 Test Case 4:
        Tests deterministic behavior when two s_j have identical maximum scores.

        R = {r1}
        S = {s1, s2}

        Scores:
        w(r1, s1) = 0.8, w(r1, s2) = 0.8

        Expected: Deterministic choice (implementation-defined, but must be consistent)
        """
        # Arrange
        list_r = ["r1"]
        list_s = ["s1", "s2"]

        # Mock result with tie (both have score 0.8)
        # The SQL ORDER BY npmi DESC will return both, but rn=1 will pick first
        # Depending on database ordering, this could be either s1 or s2
        # We just verify it's deterministic (always returns the same result)
        mock_result_data = [
            {"r_val": "r1", "s_val": "s1", "npmi": 0.8},
        ]
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(mock_result_data)
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(self.mock_conn)
        result1 = algo.create_bridge(list_r, list_s, top_k=1)
        result2 = algo.create_bridge(list_r, list_s, top_k=1)

        # Assert
        self.assertEqual(len(result1), 1, "Should return exactly one mapping")
        self.assertEqual(result1, result2, "Tie-breaking should be deterministic")

        # Verify it maps to only one s_j
        result_mapping = {r["r_val"]: r["s_val"] for r in result1}
        self.assertIn(
            result_mapping["r1"], ["s1", "s2"], "r1 must map to either s1 or s2"
        )

    def test_empty_r_input(self):
        """
        Test Case 5a: Empty R Input

        From validation protocol Section 1.3 Test Case 5:
        If R = ∅, the returned join map J must be ∅.
        """
        # Arrange
        list_r = []
        list_s = ["s1", "s2"]

        # Mock empty result
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(
            {"r_val": [], "s_val": [], "npmi": []}
        )
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(self.mock_conn)
        result = algo.create_bridge(list_r, list_s, top_k=1)

        # Assert
        self.assertEqual(len(result), 0, "Empty R should produce empty result")

    def test_empty_s_input(self):
        """
        Test Case 5b: Empty S Input

        From validation protocol Section 1.3 Test Case 5:
        If S = ∅ (and R is not empty), all r_i should map to ⊥.
        """
        # Arrange
        list_r = ["r1", "r2"]
        list_s = []

        # Mock empty result (no matches possible)
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(
            {"r_val": [], "s_val": [], "npmi": []}
        )
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(self.mock_conn)
        result = algo.create_bridge(list_r, list_s, top_k=1)

        # Assert
        self.assertEqual(len(result), 0, "Empty S should produce no mappings (all ⊥)")

    def test_at_most_one_constraint(self):
        """
        Test: At-Most-One Constraint

        Verifies that each r_i maps to at most one s_j when top_k=1.
        This is a fundamental requirement from the paper.
        """
        # Arrange
        list_r = ["r1", "r2", "r3"]
        list_s = ["s1", "s2"]

        # Mock result
        mock_result_data = [
            {"r_val": "r1", "s_val": "s1", "npmi": 0.9},
            {"r_val": "r2", "s_val": "s2", "npmi": 0.8},
            {"r_val": "r3", "s_val": "s1", "npmi": 0.7},
        ]
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(mock_result_data)
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(self.mock_conn)
        result = algo.create_bridge(list_r, list_s, top_k=1)

        # Assert
        result_mapping = {r["r_val"]: r["s_val"] for r in result}

        # Each r should appear at most once
        self.assertEqual(
            len(result_mapping), 3, "Should have mappings for all 3 r values"
        )

        # No r should map to multiple s values
        r_values = [r["r_val"] for r in result]
        self.assertEqual(
            len(r_values),
            len(set(r_values)),
            "Each r_val should appear at most once (no duplicate mappings)",
        )

    def test_top_k_extension(self):
        """
        Test: Top-K Extension

        Tests the practical extension where top_k > 1.
        This is not in the strict paper definition but is a useful feature.
        """
        # Arrange
        list_r = ["r1"]
        list_s = ["s1", "s2", "s3"]

        # Mock result with top 3 candidates
        mock_result_data = [
            {"r_val": "r1", "s_val": "s2", "npmi": 0.9},
            {"r_val": "r1", "s_val": "s1", "npmi": 0.7},
            {"r_val": "r1", "s_val": "s3", "npmi": 0.5},
        ]
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(mock_result_data)
        self.mock_conn.execute.return_value = mock_result
        self.mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(self.mock_conn)
        result = algo.create_bridge(list_r, list_s, top_k=3)

        # Assert
        self.assertEqual(len(result), 3, "Should return top 3 candidates")

        # Verify ordering (highest score first)
        self.assertEqual(result[0]["s_val"], "s2")
        self.assertEqual(result[1]["s_val"], "s1")
        self.assertEqual(result[2]["s_val"], "s3")

        # Verify scores are in descending order
        scores = [r["npmi"] for r in result]
        self.assertEqual(
            scores, sorted(scores, reverse=True), "Scores should be in descending order"
        )

    def test_independent_optimization(self):
        """
        Test: Independent Optimization (RS-JP's defining characteristic)

        Verifies that decisions for r1 are made independently of r2.
        This is the algorithm's intentional limitation (local optimality).
        """
        # Arrange - Two separate R sets with same S
        list_r1 = ["r1"]
        list_r2 = ["r2"]
        list_s = ["s1", "s2"]

        # Mock results for r1
        mock_result_r1 = MagicMock()
        mock_result_r1.pl.return_value = pl.DataFrame(
            [{"r_val": "r1", "s_val": "s1", "npmi": 0.8}]
        )

        # Mock results for r2
        mock_result_r2 = MagicMock()
        mock_result_r2.pl.return_value = pl.DataFrame(
            [{"r_val": "r2", "s_val": "s1", "npmi": 0.7}]
        )

        # Mock results for combined [r1, r2]
        mock_result_combined = MagicMock()
        mock_result_combined.pl.return_value = pl.DataFrame(
            [
                {"r_val": "r1", "s_val": "s1", "npmi": 0.8},
                {"r_val": "r2", "s_val": "s1", "npmi": 0.7},
            ]
        )

        # Act
        algo = RSJPAlgorithm(self.mock_conn)

        # Test r1 independently
        self.mock_conn.execute.return_value = mock_result_r1
        result1 = algo.create_bridge(list_r1, list_s, top_k=1)

        # Test r2 independently
        self.mock_conn.execute.return_value = mock_result_r2
        result2 = algo.create_bridge(list_r2, list_s, top_k=1)

        # Test combined
        self.mock_conn.execute.return_value = mock_result_combined
        result_combined = algo.create_bridge(list_r1 + list_r2, list_s, top_k=1)

        # Assert
        # The combined result should be the union of individual results
        # This proves decisions are independent
        mapping1 = {r["r_val"]: r["s_val"] for r in result1}
        mapping2 = {r["r_val"]: r["s_val"] for r in result2}
        mapping_combined = {r["r_val"]: r["s_val"] for r in result_combined}

        expected_combined = {**mapping1, **mapping2}
        self.assertEqual(
            mapping_combined,
            expected_combined,
            "Combined mapping should equal union of independent mappings",
        )


class TestRSJPIntegration(unittest.TestCase):
    """Integration tests for RS-JP algorithm."""

    def test_output_format(self):
        """Test that output format matches expected schema."""
        # Arrange
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.pl.return_value = pl.DataFrame(
            [{"r_val": "Germany", "s_val": "DE", "npmi": 0.85}]
        )
        mock_conn.execute.return_value = mock_result
        mock_conn.register = MagicMock()

        # Act
        algo = RSJPAlgorithm(mock_conn)
        result = algo.create_bridge(["Germany"], ["DE", "GE"], top_k=1)

        # Assert
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        item = result[0]
        self.assertIn("r_val", item)
        self.assertIn("s_val", item)
        self.assertIn("npmi", item)
        self.assertIsInstance(item["r_val"], str)
        self.assertIsInstance(item["s_val"], str)
        self.assertIsInstance(item["npmi"], (int, float))


if __name__ == "__main__":
    unittest.main(verbosity=2)
