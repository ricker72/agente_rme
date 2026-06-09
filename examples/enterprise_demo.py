from pathlib import Path

from core import OpenTibiaMapStudioEnterprise


def main() -> None:
    prompt = "Genera una expansión estilo Issavi + Roshamuul nivel 300-800."
    studio = OpenTibiaMapStudioEnterprise()
    output = studio.generate_expansion(prompt, output_path=Path("enterprise_output"))

    print("=== Enterprise Prompt ===")
    print(prompt)
    print("\n=== Result ===")
    print("Success:", output.get("success"))
    if not output.get("success"):
        print("Error:", output.get("error"))
        return

    print("Theme:", output.get("theme"))
    print("Level Range:", output.get("level_range"))
    print("Map Size:", output.get("map_size"))
    print("Lua length:", len(output.get("lua", "")))
    print("OTBM path:", output.get("otbm_path"))
    print("Template dir:", output.get("template_dir"))
    print("Quality score:", output.get("quality_report", {}).get("score"))
    print("Playtest viable:", output.get("playtest_report", {}).get("viable"))
    print("Preview keys:", list(output.get("preview", {}).keys()))
    print("Documentation title:", output.get("documentation", {}).get("title"))


if __name__ == "__main__":
    main()
