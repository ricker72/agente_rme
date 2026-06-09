"""
Tests for the CriticReport and CriticReportGenerator.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from core.critic import CriticResult, CriticReport, CriticReportGenerator
from core.critic.models import (
    CriticScore, CriticIssue, CriticRecommendation,
    IssueType, IssueSeverity, RecommendationPriority,
)


def _make_sample_result() -> CriticResult:
    return CriticResult(
        map_name="sample",
        scores={
            "visual": CriticScore("visual", 80.0, breakdown={"q": 80.0}),
            "navigation": CriticScore("navigation", 90.0),
        },
        issues=[
            CriticIssue(
                issue_type=IssueType.LOW_SPAWN_DENSITY,
                category="spawn",
                message="Low density",
                severity=IssueSeverity.WARNING,
                location="north",
            ),
        ],
        recommendations=[
            CriticRecommendation(
                title="Add spawns in north",
                description="Place more spawns in the north hunt.",
                category="spawn",
                priority=RecommendationPriority.MEDIUM,
                target_location="north",
            ),
        ],
        overall_score=85.0,
    )


class CriticReportTests(unittest.TestCase):

    def test_to_dict(self):
        r = _make_sample_result()
        report = CriticReport(result=r, generated_at="2026-06-08T00:00:00Z")
        d = report.to_dict()
        self.assertEqual(d["overall_score"], 85.0)
        self.assertEqual(d["visual_score"], 80.0)
        self.assertEqual(d["navigation_score"], 90.0)
        self.assertIn("scores", d)
        self.assertIn("issues", d)
        self.assertIn("recommendations", d)
        self.assertIn("report", d)

    def test_to_json(self):
        r = _make_sample_result()
        report = CriticReport(result=r)
        parsed = json.loads(report.to_json())
        self.assertEqual(parsed["map_name"], "sample")
        self.assertEqual(parsed["overall_score"], 85.0)

    def test_to_markdown(self):
        r = _make_sample_result()
        report = CriticReport(result=r, generated_at="2026-06-08T00:00:00Z")
        md = report.to_markdown()
        self.assertIn("Critic Report", md)
        self.assertIn("sample", md)
        self.assertIn("85.0", md)
        self.assertIn("Add spawns in north", md)

    def test_to_metrics(self):
        r = _make_sample_result()
        report = CriticReport(result=r, generated_at="2026-06-08T00:00:00Z")
        m = report.to_metrics()
        self.assertEqual(m["map_name"], "sample")
        self.assertEqual(m["overall_score"], 85.0)
        self.assertEqual(m["issue_count"], 1)
        self.assertEqual(m["recommendation_count"], 1)

    def test_write_all(self):
        r = _make_sample_result()
        report = CriticReport(result=r, generated_at="2026-06-08T00:00:00Z")
        with tempfile.TemporaryDirectory() as tmp:
            paths = report.write_all(tmp, base_name="test_report")
            for name, path in paths.items():
                self.assertTrue(os.path.exists(path), f"missing {name}")
            with open(paths["json"], encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["map_name"], "sample")
            with open(paths["metrics"], encoding="utf-8") as f:
                m = json.load(f)
            self.assertEqual(m["overall_score"], 85.0)
            self.assertTrue(os.path.getsize(paths["md"]) > 0)

    def test_report_generator(self):
        gen = CriticReportGenerator()
        report = gen.build(_make_sample_result())
        self.assertTrue(report.generated_at)
        self.assertEqual(report.version, CriticReportGenerator.VERSION)
        with tempfile.TemporaryDirectory() as tmp:
            report2 = gen.build_and_save(_make_sample_result(), tmp, base_name="x")
            self.assertTrue(os.path.exists(os.path.join(tmp, "x.json")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "x.md")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "x_metrics.json")))


if __name__ == "__main__":
    unittest.main()
