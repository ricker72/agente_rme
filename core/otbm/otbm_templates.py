from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class OtbmTemplateGenerator:
    def generate_house_xml(self, world_model: Any) -> str:
        houses = self._extract_houses(world_model)
        entries = []
        for index, house in enumerate(houses, start=1):
            entries.append(f"  <house name=\"GeneratedHouse{index}\">\n    <location x=\"{house['x']}\" y=\"{house['y']}\" z=\"{house['z']}\" />\n  </house>")
        return "<houses>\n" + "\n".join(entries) + "\n</houses>\n"

    def generate_monster_xml(self, world_model: Any) -> str:
        monsters = self._extract_monsters(world_model)
        entries = []
        for monster in monsters:
            entries.append(f"  <monster name=\"{monster['name']}\" respawn=\"{monster.get('respawn', 60)}\" />")
        return "<monsters>\n" + "\n".join(entries) + "\n</monsters>\n"

    def generate_npc_xml(self, world_model: Any) -> str:
        npcs = self._extract_npcs(world_model)
        entries = []
        for npc in npcs:
            entries.append(f"  <npc name=\"{npc['name']}\" x=\"{npc['x']}\" y=\"{npc['y']}\" z=\"{npc['z']}\" />")
        return "<npcs>\n" + "\n".join(entries) + "\n</npcs>\n"

    def generate_zones_xml(self, world_model: Any) -> str:
        zones = self._extract_zones(world_model)
        entries = []
        for index, zone in enumerate(zones, start=1):
            entries.append(
                f"  <zone id=\"{index}\" name=\"{zone['name']}\">\n    <area x1=\"{zone['x1']}\" y1=\"{zone['y1']}\" x2=\"{zone['x2']}\" y2=\"{zone['y2']}\" z=\"{zone['z']}\" />\n  </zone>"
            )
        return "<zones>\n" + "\n".join(entries) + "\n</zones>\n"

    def write_all(self, world_model: Any, base_path: Path) -> None:
        base_dir = base_path.parent
        base_name = base_path.stem
        (base_dir / f"{base_name}.house.xml").write_text(self.generate_house_xml(world_model), encoding="utf-8")
        (base_dir / f"{base_name}.monster.xml").write_text(self.generate_monster_xml(world_model), encoding="utf-8")
        (base_dir / f"{base_name}.npc.xml").write_text(self.generate_npc_xml(world_model), encoding="utf-8")
        (base_dir / f"{base_name}.zones.xml").write_text(self.generate_zones_xml(world_model), encoding="utf-8")

    def write_all_files(self, world_model: Any, destination_dir: str | Path) -> None:
        base_dir = Path(destination_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        base_name = "generated"
        (base_dir / f"{base_name}.house.xml").write_text(self.generate_house_xml(world_model), encoding="utf-8")
        (base_dir / f"{base_name}.monster.xml").write_text(self.generate_monster_xml(world_model), encoding="utf-8")
        (base_dir / f"{base_name}.npc.xml").write_text(self.generate_npc_xml(world_model), encoding="utf-8")
        (base_dir / f"{base_name}.zones.xml").write_text(self.generate_zones_xml(world_model), encoding="utf-8")

    def _extract_houses(self, world_model: Any) -> List[Dict[str, int]]:
        houses = []
        for tile in getattr(world_model, "tiles", {}).values():
            if tile.ground in {"900", "901", "902"}:
                houses.append({"x": tile.x, "y": tile.y, "z": tile.z})
        return houses[:8]

    def _extract_monsters(self, world_model: Any) -> List[Dict[str, Any]]:
        monsters = []
        for spawn in getattr(world_model, "spawns", []):
            if "monster" in spawn:
                monsters.append({"name": spawn["monster"], "respawn": spawn.get("respawn", 60)})
        for boss in getattr(world_model, "bosses", []):
            monsters.append({"name": boss.get("name", "boss"), "respawn": boss.get("respawn", 300)})
        return monsters

    def _extract_npcs(self, world_model: Any) -> List[Dict[str, Any]]:
        npcs = []
        for tile in getattr(world_model, "tiles", {}).values():
            if tile.creature and tile.creature.get("role") == "npc":
                npcs.append({"name": tile.creature.get("name", "NPC"), "x": tile.x, "y": tile.y, "z": tile.z})
        return npcs

    def _extract_zones(self, world_model: Any) -> List[Dict[str, int]]:
        zones = []
        for index, region in enumerate(getattr(world_model, "cities", []) + getattr(world_model, "dungeons", []) + getattr(world_model, "roads", []), start=1):
            x1 = region.get("x1", 0)
            y1 = region.get("y1", 0)
            x2 = region.get("x2", 0)
            y2 = region.get("y2", 0)
            z = region.get("z", 0)
            zones.append({"name": region.get("name", f"zone{index}"), "x1": x1, "y1": y1, "x2": x2, "y2": y2, "z": z})
        if not zones:
            tiles = list(getattr(world_model, "tiles", {}).values())
            if tiles:
                x_coords = [tile.x for tile in tiles]
                y_coords = [tile.y for tile in tiles]
                z_coords = [tile.z for tile in tiles]
                zones.append({"name": "generated_zone", "x1": min(x_coords), "y1": min(y_coords), "x2": max(x_coords), "y2": max(y_coords), "z": min(z_coords)})
        return zones
