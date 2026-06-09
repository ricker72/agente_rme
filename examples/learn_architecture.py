from pathlib import Path
import json

from core.architecture import ArchitectureAnalyzer, BlueprintGenerator, PatternLibrary


def main() -> None:
    source_file = Path("Ciudades.otbm")
    analyzer = ArchitectureAnalyzer()
    analyzer.pattern_library.load_blueprints("blueprints")

    if source_file.exists():
        learned = analyzer.learn_from_map(str(source_file))
        print(f"Aprendido desde {source_file}: {json.dumps(learned, ensure_ascii=False, indent=2)}")
    else:
        print("Ciudades.otbm no encontrado. Generando blueprints de ejemplo para Issavi.")
        generator = BlueprintGenerator(analyzer.pattern_library)
        generator.create_blueprint(
            "issavi_temple",
            "Temple",
            "issavi",
            [{"x": x, "y": y, "type": "floor"} for y in range(22) for x in range(22)],
            metadata={"width": 22, "height": 22, "source": "example"},
        )
        generator.create_blueprint(
            "issavi_market",
            "Market",
            "issavi",
            [{"x": x, "y": y, "type": "floor"} for y in range(18) for x in range(14)],
            metadata={"width": 14, "height": 18, "source": "example"},
        )
        learned = {
            "source": str(source_file),
            "style": "issavi",
            "blueprints": ["issavi_temple", "issavi_market"],
        }

    output_dir = Path("analysis/cities")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "ciudades_architecture_learning.json"
    output_file.write_text(json.dumps(learned, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado aprendizaje arquitectónico en {output_file}")


if __name__ == "__main__":
    main()
