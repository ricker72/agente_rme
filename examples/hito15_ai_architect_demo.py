"""
HITO 15 - AI Architect Demo
==========================

Demonstrates the AI Architect system end-to-end:
    1. Convert a free-form prompt into a WorldPlan
    2. Show all the plans (city, dungeon, hunt, boss, quest)
    3. Show the difficulty progression
    4. Show the layout
    5. Optionally execute via WorldGenerator

Examples included:
    1. The canonical example: "Issavi + 3 hunts + boss"
    2. Hybrid themes
    3. Spanish prompt
    4. Dungeon-focused prompt
    5. Integration with WorldGenerator (full pipeline)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.architect import AIArchitect
from core.architect import ai_plan


def demo_1_canonical_example():
    """Demo 1: The canonical task example."""
    print("=" * 70)
    print("  DEMO 1: Canonical example (the task spec)")
    print("=" * 70)
    print()
    architect = AIArchitect()
    p = architect.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    print(architect.explain(p))
    print()
    return p


def demo_2_hybrid_themes():
    """Demo 2: Hybrid themes."""
    print("=" * 70)
    print("  DEMO 2: Hybrid themes (Issavi + Roshamuul)")
    print("=" * 70)
    print()
    architect = AIArchitect()
    p = architect.plan("Issavi + Roshamuul level 300")
    print(f"Themes: {p.themes}")
    print(f"Primary: {p.primary_theme}")
    print(f"Cities: {[c.name for c in p.cities]}")
    print(f"Hunts:  {[h.name for h in p.hunting_zones]}")
    print(f"Roads: {len(p.roads)}, Waypoints: {len(p.waypoints)}")
    print()
    print(architect.explain(p))
    print()


def demo_3_spanish_prompt():
    """Demo 3: Spanish prompt."""
    print("=" * 70)
    print("  DEMO 3: Spanish prompt (Yalahar)")
    print("=" * 70)
    print()
    p = ai_plan("Crea una ciudad de Yalahar con 2 hunts nivel 200 y un jefe final")
    print(f"Summary: {p.summary()}")
    print(f"Themes: {p.themes}")
    print(f"Cities: {[c.name for c in p.cities]}")
    print(f"Hunts:  {[h.name for h in p.hunting_zones]}")
    print(f"Bosses: {[b.name for b in p.boss_zones]}")
    print(f"Level range: {p.level_min}-{p.level_max}")
    print()


def demo_4_dungeon_focus():
    """Demo 4: Dungeon-focused prompt."""
    print("=" * 70)
    print("  DEMO 4: Dungeon focus (Library)")
    print("=" * 70)
    print()
    p = ai_plan("Generate a library dungeon level 100-200 with 3 rooms and a boss")
    print(f"Summary: {p.summary()}")
    for d in p.dungeons:
        print(f"Dungeon: {d.name} ({d.floors} floors, {d.room_count} rooms)")
        print(f"  Difficulty: {d.difficulty}")
        if d.boss:
            print(f"  Boss: {d.boss['name']} (lvl {d.boss['level']})")
            print(f"  Mechanics: {d.boss['mechanics']}")
    print()


def demo_5_module_level_helper():
    """Demo 5: Module-level plan() helper."""
    print("=" * 70)
    print("  DEMO 5: Module-level plan() helper")
    print("=" * 70)
    print()
    p = ai_plan("Issavi level 200")
    print(f"Summary: {p.summary()}")
    print(f"Plan returned: {type(p).__name__}")
    print()


def demo_6_quest_focus():
    """Demo 6: Quest planning."""
    print("=" * 70)
    print("  DEMO 6: Quest planning")
    print("=" * 70)
    print()
    p = ai_plan("Create a Roshamuul quest level 300")
    print(f"Summary: {p.summary()}")
    for q in p.quest_zones:
        print(f"Quest: {q.title}")
        print(f"  Theme: {q.theme}")
        print(f"  Objectives ({len(q.objectives)}):")
        for obj in q.objectives:
            print(f"    [{obj['type']}] {obj['description']}")
        print(f"  NPCs: {q.npcs}")
        print(f"  Rewards: {q.rewards}")
    print()


def demo_7_with_world_generator():
    """Demo 7: Full pipeline with WorldGenerator integration."""
    print("=" * 70)
    print("  DEMO 7: Full pipeline with WorldGenerator")
    print("=" * 70)
    print()
    try:
        from core.generators import WorldGenerator
        from core.registry import AssetRegistry, BlueprintRegistry

        wg = WorldGenerator(seed=42)
        ar = AssetRegistry()
        br = BlueprintRegistry()

        architect = AIArchitect()
        architect.attach_world_generator(wg)
        architect.attach_asset_registry(ar)
        architect.attach_blueprint_registry(br)

        p = architect.plan("Generate Issavi hunt level 300")
        print(f"Summary: {p.summary()}")
        print()
        print("Integrations active:")
        for k, v in p.metadata.get("integrations", {}).items():
            print(f"  {k}: {v}")
        if "world_model_tile_count" in p.metadata:
            print(f"  Generated tiles: {p.metadata['world_model_tile_count']}")
    except Exception as e:
        print(f"  Skipped: {e}")
    print()


def demo_8_export_to_json():
    """Demo 8: Export a plan to JSON for later use."""
    print("=" * 70)
    print("  DEMO 8: Export a plan to JSON")
    print("=" * 70)
    print()
    p = ai_plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    d = p.to_dict()
    json_str = json.dumps(d, default=str, indent=2)
    # Print just the first 800 chars to avoid clutter
    print(json_str[:800] + "\n... (truncated)")
    print()
    print(f"Total JSON size: {len(json_str)} chars")
    # Save to output file
    out_path = Path(__file__).resolve().parent.parent / "output" / "hito15_plan.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json_str, encoding="utf-8")
    print(f"Saved to: {out_path}")
    print()


def main():
    """Run all demos."""
    print()
    print("#" * 70)
    print("  HITO 15 - AI ARCHITECT - FUNCTIONAL DEMOS")
    print("#" * 70)
    print()

    demo_1_canonical_example()
    demo_2_hybrid_themes()
    demo_3_spanish_prompt()
    demo_4_dungeon_focus()
    demo_5_module_level_helper()
    demo_6_quest_focus()
    demo_7_with_world_generator()
    demo_8_export_to_json()

    print("=" * 70)
    print("  ALL DEMOS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
