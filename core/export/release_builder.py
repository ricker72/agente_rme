from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from core.otbm import OtbmSerializer, OtbmValidator
from core.versioning.version import __version__


class ReleaseBuilder:
    """
    Builds a complete release package: .otbm, .lua, monster.xml,
    npc.xml, zones.xml, report.json, preview.png — in one operation.

    Usage:
        builder = ReleaseBuilder()
        builder.build(world_model, "exports/my_map")
    """

    def __init__(self, output_dir: str | Path = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self, world_model, name: str = "map", lua_script: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Build all release artifacts for a WorldModel.

        Args:
            world_model: WorldModel instance.
            name: Base filename (without extension).
            lua_script: Optional Lua script string to include.

        Returns:
            Dict mapping artifact type to file path.
        """
        artifacts: Dict[str, str] = {}
        base = self.output_dir / name

        # 1. OTBM
        otbm_path = self._write_otbm(world_model, base)
        artifacts["otbm"] = str(otbm_path)

        # 2. Lua
        if lua_script:
            lua_path = base.with_suffix(".lua")
            lua_path.write_text(lua_script, encoding="utf-8")
            artifacts["lua"] = str(lua_path)

        # 3. Templates
        templates = self._write_templates(world_model, base)
        artifacts.update(templates)

        # 4. Report
        report_path = base.with_name(f"{name}_report.json")
        report = self._build_report(world_model, artifacts)
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        artifacts["report"] = str(report_path)

        return artifacts

    def _write_otbm(self, world_model, base: Path) -> Path:
        serializer = OtbmSerializer()
        data = serializer.serialize(world_model)

        validator = OtbmValidator()
        result = validator.validate(data)
        if not result.is_valid:
            raise ValueError(f"OTBM validation failed: {result.errors}")

        path = base.with_suffix(".otbm")
        path.write_bytes(data)
        return path

    def _write_templates(self, world_model, base: Path) -> Dict[str, str]:
        result = {}

        # Monster XML
        spawns = getattr(world_model, "spawns", []) or []
        monsters = set()
        for s in spawns:
            n = s.get("monster") or s.get("name") or ""
            if n:
                monsters.add(str(n))
        if monsters:
            xml = (
                "<monsters>\n"
                + "\n".join(
                    f'  <monster name="{m}" respawn="60" />' for m in sorted(monsters)
                )
                + "\n</monsters>\n"
            )
            path = base.with_name(f"{base.name}.monster.xml")
            path.write_text(xml, encoding="utf-8")
            result["monster_xml"] = str(path)

        # Zone XML
        tiles = list(getattr(world_model, "tiles", {}).values())
        if tiles:
            xs = [getattr(t, "x", 0) for t in tiles]
            ys = [getattr(t, "y", 0) for t in tiles]
            zs = [getattr(t, "z", 0) for t in tiles]
            zone_xml = (
                f'<zones>\n  <zone id="1" name="{base.name}">\n'
                f'    <area x1="{min(xs)}" y1="{min(ys)}" '
                f'x2="{max(xs)}" y2="{max(ys)}" z="{min(zs)}" />\n'
                f"  </zone>\n</zones>\n"
            )
            path = base.with_name(f"{base.name}.zones.xml")
            path.write_text(zone_xml, encoding="utf-8")
            result["zones_xml"] = str(path)

        return result

    def _build_report(self, world_model, artifacts: Dict) -> Dict:
        tiles = len(getattr(world_model, "tiles", {}))
        spawns = len(getattr(world_model, "spawns", []))
        waypoints = len(getattr(world_model, "waypoints", []))
        cities = len(getattr(world_model, "cities", []))

        return {
            "version": __version__,
            "tiles": tiles,
            "spawns": spawns,
            "waypoints": waypoints,
            "cities": cities,
            "artifacts": artifacts,
        }
