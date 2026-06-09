from __future__ import annotations

from typing import Any, Dict, List

from core.compiler import LuaCompiler
from core.quality.map_reviewer import MapReviewer


class LuaGenerator:
    def generate(self, world_model: Any) -> str:
        lines: List[str] = [
            "if not app.hasMap() then",
            "    return",
            "end",
            "",
            "app.transaction(function(map)",
        ]

        for tile in world_model.tiles.values():
            lines.append(f"    local tile = map:getOrCreateTile({tile.x}, {tile.y}, {tile.z})")
            lines.append(f"    tile.ground = \"{tile.ground}\"")
            for item in tile.items:
                lines.append(f"    tile:addItem({item.get('id', 0)})")
            if tile.spawn:
                lines.append(f"    tile:setSpawn(\"{tile.spawn.get('monster', 'unknown')}\")")
            if tile.creature:
                lines.append(f"    tile:setCreature(\"{tile.creature.get('name', 'unknown')}\")")
            if tile.decorations:
                lines.append("    tile:borderize()")

        lines.append("end")
        lines.append("end")
        return "\n".join(lines)


class ExportPipeline:
    def __init__(self):
        self.lua_generator = LuaGenerator()
        self.compiler = LuaCompiler()
        self.reviewer = MapReviewer()

    def validate_quality(self, world_model: Any) -> Dict[str, Any]:
        review = self.reviewer.review(world_model)
        if review["score"] < self.reviewer.threshold:
            review = self.reviewer.improve(world_model)

        if review["score"] < self.reviewer.threshold:
            raise RuntimeError(
                f"Map quality score {review['score']} is below the minimum threshold of {self.reviewer.threshold}. "
                f"Review issues: {review['accessibility_issues'] + review['design_issues'] + review['progression_issues']}"
            )

        return review

    def convert(self, world_model: Any) -> str:
        self.validate_quality(world_model)
        source = self.lua_generator.generate(world_model)
        report = self.compiler.compile(source)
        if report.status != "success":
            raise RuntimeError(f"Lua compiler failure: {report.errors}")
        return report.script
