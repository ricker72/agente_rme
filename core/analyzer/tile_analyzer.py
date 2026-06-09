from collections import Counter, defaultdict
from typing import Dict, List

GROUND_LOOKUP = {
    393: "sandstone_floor",
    415: "polished_stone",
    416: "mossy_stone",
    1053: "roshamuul_floor",
    1056: "roshamuul_stone",
    396: "yalahar_floor",
}


class TileAnalyzer:
    def analyze_xml_tiles(self, root) -> Dict[str, int]:
        counts = Counter()
        for tile in root.findall("map/tile"):
            ground_id = int(tile.get("ground", 0)) if tile.get("ground") else 0
            name = GROUND_LOOKUP.get(ground_id, f"tile_{ground_id}")
            counts[name] += 1
            for item in tile.findall("item"):
                counts[f"item_{item.get('id', 'unknown')}"] += 1
        return dict(counts)

    def summarize_binary_tiles(self, raw: bytes) -> Dict[str, int]:
        counts = defaultdict(int)
        for tag, name in GROUND_LOOKUP.items():
            if bytes(str(tag), "utf-8") in raw:
                counts[name] += raw.count(bytes(str(tag), "utf-8"))
        return dict(counts)

    def summarize_ground_usage(self, tiles: List[Dict[str, int]]) -> Dict[str, int]:
        counts = Counter()
        for tile in tiles:
            counts.update(tile)
        return dict(counts)
