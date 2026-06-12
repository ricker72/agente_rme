"""
Tests for the ScoreCalculator.
"""

from __future__ import annotations

import unittest

from core.critic import ScoreCalculator
from core.critic.models import CriticScore, CriticIssue, IssueSeverity


class ScoreCalculatorTests(unittest.TestCase):
    def test_combine_empty(self):
        calc = ScoreCalculator()
        self.assertEqual(calc.combine({}), 0.0)

    def test_combine_single(self):
        calc = ScoreCalculator()
        self.assertEqual(calc.combine({"visual": 80.0}), 80.0)

    def test_combine_renormalized(self):
        calc = ScoreCalculator()
        # Only visual and navigation supplied — renormalized to 0.5/0.5
        # 0.12*80 + 0.12*100 / (0.12+0.12) = 90.0
        result = calc.combine({"visual": 80.0, "navigation": 100.0})
        self.assertAlmostEqual(result, 90.0, places=6)

    def test_combine_all_categories(self):
        calc = ScoreCalculator()
        scores = {cat: 80.0 for cat in ScoreCalculator.weights}
        result = calc.combine(scores)
        self.assertEqual(result, 80.0)

    def test_combine_scores_object(self):
        calc = ScoreCalculator()
        scores = {
            "visual": CriticScore("visual", 70.0),
            "navigation": CriticScore("navigation", 90.0),
        }
        # 0.12*70 + 0.12*90 / 0.24 = 80.0
        self.assertAlmostEqual(calc.combine_scores(scores), 80.0, places=6)

    def test_penalized(self):
        calc = ScoreCalculator()
        scores = {cat: 80.0 for cat in ScoreCalculator.weights}
        result = calc.penalized(scores, 20.0)
        self.assertEqual(result, 60.0)

    def test_issues_penalty_sum(self):
        issues = [
            CriticIssue(
                issue_type="empty_region",
                category="x",
                message="a",
                severity=IssueSeverity.WARNING,
            ),
            CriticIssue(
                issue_type="isolated_region",
                category="x",
                message="b",
                severity=IssueSeverity.CRITICAL,
            ),
            CriticIssue(
                issue_type="dead_end",
                category="x",
                message="c",
                severity=IssueSeverity.INFO,
            ),
        ]
        # 5 + 20 + 1 = 26
        self.assertEqual(ScoreCalculator.issues_penalty(issues), 26.0)

    def test_issues_penalty_empty(self):
        self.assertEqual(ScoreCalculator.issues_penalty([]), 0.0)

    def test_issues_penalty_dict(self):
        issues = [{"penalty": 7.5}, {"penalty": 2.5}]
        self.assertEqual(ScoreCalculator.issues_penalty(issues), 10.0)

    def test_clamp_bounds(self):
        calc = ScoreCalculator()
        scores = {cat: 50.0 for cat in ScoreCalculator.weights}
        # Massive penalty clamps to 0
        result = calc.penalized(scores, 1000.0, max_penalty=200.0)
        self.assertEqual(result, 0.0)
        # Negative penalty should be ignored
        result = calc.penalized(scores, -50.0, max_penalty=200.0)
        self.assertEqual(result, 50.0)

    def test_custom_weights(self):
        custom = {"visual": 1.0}
        calc = ScoreCalculator(weights=custom)
        # Only visual counts
        self.assertEqual(calc.combine({"visual": 70.0, "navigation": 0.0}), 70.0)


if __name__ == "__main__":
    unittest.main()
