from pathlib import Path

from core.planner import AIPlanner
from core.world_engine import WorldEngine
from core.otbm import OtbmWriter


def main() -> None:
    prompt = "Generate a compact hybrid dungeon map with a central boss arena and natural caves."
    planner = AIPlanner()
    world_plan = planner.plan(prompt)

    engine = WorldEngine()
    world_model = engine.build(world_plan)

    output_path = Path(__file__).resolve().parent / "generated_world.otbm"
    writer = OtbmWriter()
    otbm_path = writer.write(world_model, output_path, generate_templates=True)

    print(f"OTBM exported to: {otbm_path}")
    print(f"House/NPC/Monster/Zones templates generated alongside {otbm_path.name}")


if __name__ == "__main__":
    main()
