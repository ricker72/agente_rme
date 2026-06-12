"""Smoke test for the knowledge subsystem."""

import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from core.knowledge import (
    KnowledgeEngine,
    build_metrics,
    parse_query,
)


def main():
    src1 = {
        "meta": {"name": "roshamuul", "theme": "roshamuul"},
        "regions": [
            {
                "name": "roshamuul_circular_hunt",
                "theme": "roshamuul",
                "min_level": 280,
                "max_level": 380,
                "tags": ["circular", "soul_war"],
            },
            {
                "name": "roshamuul_outer",
                "theme": "roshamuul",
                "min_level": 250,
                "max_level": 350,
            },
        ],
        "cities": [
            {"name": "Issavi", "theme": "issavi", "min_level": 250, "max_level": 450}
        ],
        "structures": [
            {
                "name": "roshamuul_boss_arena",
                "category": "boss_room",
                "theme": "roshamuul",
                "min_level": 300,
                "max_level": 500,
                "width": 30,
                "height": 30,
                "tags": ["boss", "circular", "arena"],
            }
        ],
        "spawns": [
            {"monster": "Guzzlemaw", "zone": "roshamuul_circular_hunt", "level": 280},
            {"monster": "Hellflayer", "zone": "roshamuul_circular_hunt", "level": 320},
        ],
        "waypoints": [{"name": "roshamuul_tp", "theme": "roshamuul"}],
        "quests": [
            {
                "name": "Soul War",
                "theme": "roshamuul",
                "min_level": 250,
                "max_level": 500,
                "difficulty": "hard",
                "style": "linear",
            }
        ],
    }
    src2 = {
        "meta": {"name": "issavi", "theme": "issavi"},
        "regions": [
            {
                "name": "issavi_sewers_hunt",
                "theme": "issavi",
                "min_level": 250,
                "max_level": 400,
                "tags": ["sewer"],
            },
            {
                "name": "issavi_desert_hunt",
                "theme": "issavi",
                "min_level": 280,
                "max_level": 380,
            },
        ],
        "cities": [{"name": "Issavi_City_Center", "theme": "issavi"}],
        "spawns": [{"monster": "Scarab", "zone": "issavi_sewers_hunt", "level": 280}],
        "quests": [
            {"name": "Issavi Main Quest", "theme": "issavi", "difficulty": "medium"}
        ],
    }
    src3 = {
        "meta": {"name": "soul_war", "theme": "roshamuul"},
        "regions": [
            {
                "name": "soul_war_surface",
                "theme": "roshamuul",
                "min_level": 250,
                "max_level": 500,
                "tags": ["soul_war", "circular"],
            },
        ],
        "structures": [
            {
                "name": "soul_war_boss_arena",
                "category": "arena",
                "tags": ["boss", "circular"],
                "width": 40,
                "height": 40,
                "min_level": 250,
                "max_level": 500,
            }
        ],
        "raids": [{"name": "Ferumbras Raid", "theme": "generic", "min_level": 300}],
        "spawns": [{"monster": "Guzzlemaw", "zone": "soul_war_surface", "level": 320}],
    }
    engine = KnowledgeEngine.build_from_sources([src1, src2, src3])
    print("Total entries:", engine.dataset.total())
    print("Hunts:", [h.name for h in engine.dataset.hunts])
    print("Cities:", [c.name for c in engine.dataset.cities])
    print("Boss rooms:", [b.name for b in engine.dataset.boss_rooms])
    print("Quests:", [q.name for q in engine.dataset.quests])
    print("Raids:", [r.name for r in engine.dataset.raids])
    print("Biomes:", [b.name for b in engine.dataset.biomes])
    print()
    print("--- Find similar hunts roshamuul_circular_hunt (exact) ---")
    for s in engine.find_similar_hunts("roshamuul_circular_hunt", k=5):
        print(s)
    print()
    print("--- Find similar cities Issavi ---")
    for s in engine.find_similar_cities("Issavi", k=5):
        print(s)
    print()
    print("--- Query: 'boss rooms with circular arena' ---")
    for s in engine.query_text("boss rooms with circular arena", k=5).matches:
        print(" ", s.entry.name, s.score)
    print()
    metrics = build_metrics(engine.dataset)
    print("Metrics:", json.dumps(metrics.to_dict(), indent=2))
    cat = engine.build_catalog(top_n=5)
    print("Catalog top hunts:", [c["name"] for c in cat.top_hunts])
    print()
    out = os.path.join(tempfile.gettempdir(), "kds.json")
    engine.save(out)
    print("Saved to:", out)
    print()
    parsed = parse_query("hunts with circular routes level 300-500")
    print(
        "Parsed query:",
        parsed.entry_type,
        parsed.min_level,
        parsed.max_level,
        parsed.attrs,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
