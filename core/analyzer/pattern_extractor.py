import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class Pattern:
    pattern: str
    source: str
    width: int
    height: int
    style: str
    floors: List[int]
    ground_stats: Dict[str, int]
    wall_stats: Dict[str, int]
    decoration_stats: Dict[str, int]
    metadata: Dict[str, object]


class PatternExtractor:
    def extract_pattern(
        self,
        source: str,
        style: str,
        tile_stats: Dict[str, int],
        width: int,
        height: int,
        floors: Optional[List[int]] = None,
    ) -> Dict[str, object]:
        floors = floors or []
        pattern = Pattern(
            pattern=source.replace(".", "_").lower(),
            source=source,
            width=width,
            height=height,
            style=style,
            floors=floors,
            ground_stats={k: v for k, v in tile_stats.items() if "tile_" not in k},
            wall_stats={
                k: v for k, v in tile_stats.items() if "wall" in k or "tile_" in k
            },
            decoration_stats={
                k: v for k, v in tile_stats.items() if "decoration" in k or "tile_" in k
            },
            metadata={"tile_count": sum(tile_stats.values())},
        )
        return asdict(pattern)

    def save_pattern(self, pattern: Dict[str, object], path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(pattern, handle, ensure_ascii=False, indent=2)
