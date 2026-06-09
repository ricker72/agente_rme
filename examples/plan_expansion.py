from core.planner import AIPlanner
from core.world_engine import WorldEngine


def main() -> None:
    prompt = "Genera una expansión nivel 300-500 inspirada en Issavi y Roshamuul."
    planner = AIPlanner()
    world_engine = WorldEngine()
    plan = planner.plan(prompt)

    print("=== Prompt ===")
    print(prompt)
    print("\n=== World Plan ===")
    print(plan["world_plan"])
    print("\n=== Size Estimate ===")
    print(plan["size_estimate"])
    print("\n=== Validation ===")
    print("Valid:", plan["plan_valid"])
    print(plan["validation"])

    if plan["plan_valid"]:
        world_model = world_engine.build(plan["world_plan"])
        lua_output = world_engine.export(world_model)
        print("\n=== Generated Lua ===")
        print(lua_output)
    else:
        print("No se puede generar el mundo: plan inválido.")


if __name__ == "__main__":
    main()
