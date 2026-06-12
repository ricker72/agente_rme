"""Integration test that knowledge entries can be enriched from blueprints."""

from __future__ import annotations

import unittest

from core.knowledge import DatasetBuilder


class _StubBlueprint:
    """Stand-in for a Blueprint-like object."""

    def __init__(self, name: str, theme: str, category: str):
        self.name = name
        self.theme = theme
        self.category = category

    def to_dict(self) -> dict:
        # Real blueprints return their full data including structures.
        return {
            "name": self.name,
            "theme": self.theme,
            "category": self.category,
            "min_level": 200,
            "max_level": 500,
            "structures": [
                {
                    "name": self.name,
                    "category": self.category,
                    "theme": self.theme,
                    "min_level": 200,
                    "max_level": 500,
                    "width": 30,
                    "height": 30,
                },
            ],
        }


class TestKnowledgeBlueprintIntegration(unittest.TestCase):
    def test_blueprint_like_object_yields_entries(self):
        bp = _StubBlueprint("issavi_temple", "issavi", "temple")
        builder = DatasetBuilder()
        ds = builder.build_from_sources([bp])
        # The city extractor picks up structures with category='temple'.
        names = [e.name for e in ds.all_entries()]
        self.assertIn("issavi_temple", names)

    def test_blueprint_dict_with_more_data(self):
        # Some blueprints may have a richer dict shape with meta info.
        bp_dict = {
            "meta": {"name": "issavi_temple_full", "theme": "issavi"},
            "name": "issavi_temple_full",
            "theme": "issavi",
            "category": "temple",
            "min_level": 200,
            "max_level": 500,
            "size": [30, 30],
            "tags": ["temple", "desert"],
            "structures": [
                {
                    "name": "issavi_temple_full",
                    "category": "temple",
                    "theme": "issavi",
                    "min_level": 200,
                    "max_level": 500,
                    "width": 30,
                    "height": 30,
                },
            ],
        }
        builder = DatasetBuilder()
        ds = builder.build_from_sources([bp_dict])
        entry = ds.by_name("issavi_temple_full")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.biome, "issavi")
        self.assertEqual(entry.min_level, 200)


if __name__ == "__main__":
    unittest.main()
