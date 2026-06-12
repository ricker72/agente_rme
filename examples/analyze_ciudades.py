from pathlib import Path
import json

from core.analyzer import MapAnalyzer, DatasetBuilder


def main() -> None:
    source_file = Path("Ciudades.otbm")
    output_file = Path("analysis/cities/ciudades.json")
    analyzer = MapAnalyzer()

    if source_file.exists():
        analysis = analyzer.analyze(str(source_file))
        print(f"Analyzed {source_file}: {analysis}")
    else:
        print("Ciudades.otbm no encontrado. Generando análisis de ejemplo.")
        analysis = {
            "source": "Ciudades.otbm",
            "type": "unknown",
            "size": {"width": 150, "height": 120},
            "tile_summary": {"floor": 6200, "walls": 950, "water": 180},
            "room_count": 24,
            "style": "issavi-inspired",
            "monster_density": 0.13,
            "spawn_regions": [
                {
                    "area": "northeast_gate",
                    "monsters": ["witch", "orc"],
                    "density": 0.12,
                },
                {
                    "area": "central_plaza",
                    "monsters": ["minotaur", "gnarlhound"],
                    "density": 0.18,
                },
            ],
        }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved analysis to {output_file}")

    dataset_builder = DatasetBuilder(root="analysis")
    dataset_builder.build_from_analysis(analysis, category="cities", name="ciudades")
    print("Dataset builder processed analysis into analysis/cities/ciudades.json")


if __name__ == "__main__":
    main()
