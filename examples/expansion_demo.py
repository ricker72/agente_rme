from core.planner import AIPlanner


def main() -> None:
    prompt = "Genera una expansión endgame inspirada en Issavi y Roshamuul."
    planner = AIPlanner()
    result = planner.plan(prompt)

    expansion = result.get("expansion", {})
    print("=== Expansion Designer Output ===")
    print(f"Name: {expansion.get('name')}")
    print(f"Theme: {expansion.get('theme')}")
    print(f"Cities: {len(expansion.get('cities', []))}")
    print(f"Hunts: {len(expansion.get('hunts', []))}")
    print(f"Dungeons: {len(result.get('world_plan', {}).get('dungeons', []))}")
    print(f"Bosses: {len(expansion.get('bosses', []))}")
    print(f"Quests: {len(expansion.get('quests', []))}")
    print(f"Rewards: {list(expansion.get('rewards', {}).keys())}")
    print(
        f"Progression tiers: {[tier['name'] for tier in expansion.get('progression', {}).get('tiers', [])]}\n"
    )

    print("=== Lore ===")
    for key, value in expansion.get("lore", {}).items():
        print(f"{key}: {value}")

    print("\n=== World Plan Summary ===")
    world_plan = result.get("world_plan", {})
    print(f"Cities: {len(world_plan.get('cities', []))}")
    print(f"Hunting zones: {len(world_plan.get('hunting_zones', []))}")
    print(f"Boss zones: {len(world_plan.get('boss_zones', []))}")
    print(f"Quest zones: {len(world_plan.get('quest_zones', []))}")


if __name__ == "__main__":
    main()
