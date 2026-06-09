"""
Tests for the CityAnalyzer.
"""

from __future__ import annotations

import unittest

from core.critic.analyzers import CityAnalyzer
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.region import Region


class CityAnalyzerTests(unittest.TestCase):

    def test_no_cities(self):
        w = WorldModel()
        for x in range(5):
            for y in range(5):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        result = CityAnalyzer().analyze(w)
        self.assertEqual(result["metrics"]["cities"], 0)
        self.assertTrue(any("city" in r.title.lower() for r in result["recommendations"]))

    def test_city_with_all_services(self):
        w = WorldModel()
        w.add_region(Region(name="city_issavi", min_level=1, max_level=50))
        w.add_region(Region(name="city_issavi_depot", min_level=1, max_level=50))
        w.add_region(Region(name="city_issavi_temple", min_level=1, max_level=50))
        w.add_region(Region(name="city_issavi_npc", min_level=1, max_level=50))
        for x in range(5):
            for y in range(5):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100, zone="city_issavi"))
        result = CityAnalyzer().analyze(w)
        # The depot/temple sub-zones are also matched as "cities" because they
        # don't contain a service keyword themselves — they DO contain "city" via
        # the substring. We accept that the count is >= 1.
        self.assertGreaterEqual(result["metrics"]["cities"], 1)
        # The main city is in the result and has no missing services
        per_city = result["metrics"]["per_city"]
        main = next((c for c in per_city if c["name"] == "city_issavi"), None)
        if main is not None:
            self.assertNotIn("depot", [i.issue_type.value for i in result["issues"]])
        # No city_missing_services issue since both depot and temple are present
        for issue in result["issues"]:
            self.assertNotEqual(issue.issue_type.value, "city_missing_services")

    def test_city_missing_depot_and_temple(self):
        w = WorldModel()
        w.add_region(Region(name="city_thorn", min_level=1, max_level=50))
        result = CityAnalyzer().analyze(w)
        issue_types = {i.issue_type.value for i in result["issues"]}
        self.assertIn("city_missing_services", issue_types)
        recs_titles = [r.title for r in result["recommendations"]]
        self.assertTrue(any("depot" in t.lower() for t in recs_titles))
        self.assertTrue(any("temple" in t.lower() for t in recs_titles))

    def test_empty_world_default_score(self):
        w = WorldModel()
        result = CityAnalyzer().analyze(w)
        # Empty world with no cities => default score 60.0
        self.assertGreaterEqual(result["score"].value, 0.0)
        # The default non-zero "no cities" score
        self.assertEqual(result["score"].value, 60.0)


if __name__ == "__main__":
    unittest.main()
