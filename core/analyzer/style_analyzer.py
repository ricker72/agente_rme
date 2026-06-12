from typing import Dict, List

STYLE_SIGNATURES = {
    "issavi": ["sandstone_floor", "polished_stone", "mossy_stone"],
    "roshamuul": ["roshamuul_floor", "polished_stone"],
    "library": ["sandstone_floor", "polished_stone", "tile_2148"],
    "yalahar": ["yalahar_floor", "water", "polished_stone"],
    "ankrahmun": ["sandstone_floor", "tile_2150"],
    "darashia": ["water", "polished_stone"],
    "soulwar": ["roshamuul_floor", "tile_2152"],
}


class StyleAnalyzer:
    def detect_style(self, tile_stats: Dict[str, int]) -> str:
        if not tile_stats:
            return "unknown"
        scores = {style: 0 for style in STYLE_SIGNATURES}
        for style, markers in STYLE_SIGNATURES.items():
            for marker in markers:
                scores[style] += tile_stats.get(marker, 0)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "unknown"

    def summarize_style(
        self, tile_stats: Dict[str, int], house_data: List[Dict[str, object]]
    ) -> Dict[str, object]:
        return {
            "dominant_style": self.detect_style(tile_stats),
            "top_tiles": sorted(
                tile_stats.items(), key=lambda item: item[1], reverse=True
            )[:10],
            "house_count": len(house_data),
        }
