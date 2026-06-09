"""
MVP V0.1 — Pipeline Runner
End-to-end functional pipeline:

    Prompt -> Interpreter -> Theme Resolver -> Hunt Generator
    -> Spawn Generator -> Lua Generator -> Validator -> Preview

Usage:
    python pipeline_runner.py "Genera una zona Issavi + Roshamuul nivel 300-500"
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class PipelineReport:
    prompt: str = ""
    success: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    outputs: Dict[str, str] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)


class PipelineRunner:
    """
    Orchestrates the complete MVP V0.1 pipeline.

    Stages:
    1. PromptInterpreter   -> intent
    2. ThemeResolver        -> theme_data
    3. HuntGenerator        -> hunt_area
    4. SpawnGenerator       -> spawn_plan
    5. LuaGenerator         -> lua_script
    6. LuaValidator         -> validation_report
    7. PreviewGenerator     -> preview.png
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, prompt: str) -> PipelineReport:
        report = PipelineReport(prompt=prompt)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n{'='*60}")
        print(f"  OpenTibiaBR RME Map Generator - MVP V0.1")
        print(f"{'='*60}")
        print(f"\n  Prompt: {prompt}")
        print(f"  Timestamp: {timestamp}\n")

        try:
            # -- Stage 1: Prompt Interpreter --
            print("[1/7] Interpretando prompt...")
            intent = self._stage1_interpret(prompt)
            report.stats["intent"] = {
                "theme": intent.theme,
                "level_range": intent.level_range,
                "type": intent.type,
            }
            print(f"       Temas: {intent.theme}")
            print(f"       Nivel: {intent.level_range}")
            print(f"       Tipo:  {intent.type}")

            # -- Stage 2: Theme Resolver --
            print("[2/7] Resolviendo temas...")
            theme_data = self._stage2_resolve_themes(intent)
            report.stats["themes"] = [t.name for t in theme_data]
            for t in theme_data:
                print(f"       {t.name}: {len(t.grounds)} grounds, {len(t.walls)} walls, "
                      f"{len(t.monsters)} monsters")

            # -- Branch: City vs Dungeon vs Hunt --
            if intent.type == "city":
                hunt_area = None
                spawn_plan = None
                lua_script = None

                # Stage 3: City Generator
                print("[3/7] Generando ciudad...")
                city_model = self._stage3city_generate_city(intent, theme_data)
                report.stats["city"] = {
                    "name": city_model.name,
                    "theme": city_model.theme,
                    "districts": len(city_model.districts),
                    "buildings": len(city_model.buildings),
                    "roads": len(city_model.roads),
                    "waypoints": len(city_model.waypoints),
                }
                print(f"       {city_model.name}: {len(city_model.districts)} districts, "
                      f"{len(city_model.buildings)} buildings, {len(city_model.roads)} roads")

                # Stage 4: Convertir City → WorldModel
                print("[4/7] Convirtiendo City -> WorldModel...")
                world_model = self._stage4city_convert(city_model)
                report.stats["city_wm"] = {
                    "tiles": len(world_model.tiles),
                }
                print(f"       {len(world_model.tiles)} tiles generados")

                # Skips Lua stages for city
                stage_complete = "city"

                # Validación (skipped for city)
                report.stats["validation"] = {"is_valid": True, "status": "skipped (city)"}

                # OTBM Export directa (saltando Lua)
                print("[7.5] Exportando OTBM (city)...")
                otbm_path = self._stage5city_otbm(world_model, intent, timestamp)
                if otbm_path:
                    report.outputs["otbm"] = str(otbm_path)
                    print(f"       OTBM: {otbm_path}")

                # Report data
                report_json_path = self.output_dir / "report.json"
                report_data = {
                    "prompt": prompt,
                    "timestamp": timestamp,
                    "type": "city",
                    "intent": report.stats.get("intent", {}),
                    "themes": report.stats.get("themes", []),
                    "city": report.stats.get("city", {}),
                    "city_wm": report.stats.get("city_wm", {}),
                    "success": len(report.errors) == 0,
                    "errors": report.errors,
                    "warnings": report.warnings,
                }
                with open(report_json_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                report.outputs["report"] = str(report_json_path)
                print(f"       -> {report_json_path}")

                report.success = len(report.errors) == 0
                ascii_preview = "(city — sin preview ASCII)"

            elif intent.type == "dungeon":
                hunt_area = None
                spawn_plan = None
                lua_script = None

                # Stage 3: Dungeon Generator
                print("[3/7] Generando dungeon multinivel...")
                dungeon_model = self._stage3dungeon_generate(intent, theme_data)
                report.stats["dungeon"] = {
                    "name": dungeon_model.name,
                    "theme": dungeon_model.theme,
                    "floors": len(dungeon_model.floors),
                    "rooms": len(dungeon_model.rooms),
                    "bosses": len(dungeon_model.bosses),
                    "shortcuts": len(dungeon_model.shortcuts),
                    "spawns": len(dungeon_model.spawns),
                }
                print(f"       {dungeon_model.name}: {len(dungeon_model.floors)} floors, "
                      f"{len(dungeon_model.rooms)} rooms, "
                      f"{len(dungeon_model.bosses)} bosses")

                # Stage 4: Convertir Dungeon -> WorldModel
                print("[4/7] Convirtiendo Dungeon -> WorldModel...")
                world_model = self._stage4dungeon_convert(dungeon_model)
                report.stats["dungeon_wm"] = {
                    "tiles": len(world_model.tiles),
                    "floors": len(set(getattr(t, "z", 7) for t in world_model.tiles.values())),
                }
                print(f"       {len(world_model.tiles)} tiles, "
                      f"{report.stats['dungeon_wm']['floors']} floors")

                # Stage 5: Dungeon OTBM Export
                print("[5/7] Exportando dungeon OTBM...")
                otbm_path = self._stage5dungeon_otbm(world_model, intent, dungeon_model, timestamp)
                if otbm_path:
                    report.outputs["otbm"] = str(otbm_path)
                    print(f"       OTBM: {otbm_path}")

                report.stats["validation"] = {"is_valid": True, "status": "skipped (dungeon)"}

                report_json_path = self.output_dir / "report.json"
                report_data = {
                    "prompt": prompt,
                    "timestamp": timestamp,
                    "type": "dungeon",
                    "intent": report.stats.get("intent", {}),
                    "themes": report.stats.get("themes", []),
                    "dungeon": report.stats.get("dungeon", {}),
                    "dungeon_wm": report.stats.get("dungeon_wm", {}),
                    "success": len(report.errors) == 0,
                    "errors": report.errors,
                    "warnings": report.warnings,
                }
                with open(report_json_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                report.outputs["report"] = str(report_json_path)
                print(f"       -> {report_json_path}")

                report.success = len(report.errors) == 0
                ascii_preview = "(dungeon multinivel — sin preview ASCII)"

            else:
                # -- Stage 3: Hunt Generator --
                print("[3/7] Generando area de hunt...")
                hunt_area = self._stage3_generate_hunt(intent, theme_data)
                report.stats["hunt"] = {
                    "width": hunt_area.width,
                    "height": hunt_area.height,
                    "rooms": len(hunt_area.rooms),
                    "tiles": len(hunt_area.tiles),
                }
                print(f"       {hunt_area.width}x{hunt_area.height} tiles, "
                      f"{len(hunt_area.rooms)} rooms")

                # -- Stage 4: Spawn Generator --
                print("[4/7] Generando spawns...")
                spawn_plan = self._stage4_generate_spawns(hunt_area, theme_data, intent)
                report.stats["spawns"] = {
                    "total": len(spawn_plan.spawns),
                    "boss": bool(spawn_plan.boss_spawn),
                }
                print(f"       {len(spawn_plan.spawns)} spawns "
                      f"(boss: {'Si' if spawn_plan.boss_spawn else 'No'})")

                # -- Stage 5: Lua Generator --
                print("[5/7] Generando script Lua...")
                lua_script = self._stage5_generate_lua(hunt_area, spawn_plan, intent)
                report.stats["lua"] = {
                    "tile_count": lua_script.tile_count,
                    "spawn_count": lua_script.spawn_count,
                    "creature_count": lua_script.creature_count,
                    "border_count": lua_script.border_count,
                }
                print(f"       {lua_script.tile_count} tiles, "
                      f"{lua_script.spawn_count} spawns")

                stage_complete = "hunt"

                # -- Stage 6: Validation --
                print("[6/7] Validando script Lua...")
                validation_report = self._stage6_validate(lua_script)
                report.stats["validation"] = {
                    "is_valid": validation_report.is_valid,
                    "errors": len(validation_report.errors),
                    "warnings": len(validation_report.warnings),
                    "stats": validation_report.stats,
                }
                status = "APROBADO" if validation_report.is_valid else "CON ERRORES"
                print(f"       [{status}] ({len(validation_report.errors)} errores, "
                      f"{len(validation_report.warnings)} warnings)")

                for err in validation_report.errors:
                    report.errors.append(f"[L{err.line}] {err.message}")
                    print(f"         ERR: {err.message}")
                for warn in validation_report.warnings:
                    report.warnings.append(f"[L{warn.line}] {warn.message}")

                # -- Stage 7: Preview --
                print("[7/7] Generando preview...")
                preview_path = self._stage7_preview(hunt_area, intent, timestamp)
                if preview_path:
                    print(f"       Preview: {preview_path}")

                # -- Stage 7.5: OTBM Export --
                print("[7.5] Exportando OTBM...")
                otbm_path = self._stage8_export_otbm(hunt_area, spawn_plan, intent, timestamp)
                if otbm_path:
                    print(f"       OTBM: {otbm_path}")

                # -- Write outputs --
                print("\n-- Escribiendo archivos de salida --")

                base_name = f"{'_'.join(intent.theme) if intent.theme else 'map'}"
                if not base_name:
                    base_name = "map"

                # Lua file
                lua_path = self.output_dir / f"{base_name}.lua"
                with open(lua_path, "w", encoding="utf-8") as f:
                    f.write(lua_script.code)
                report.outputs["lua"] = str(lua_path)
                print(f"       -> {lua_path}")

                # OTBM file
                if otbm_path:
                    report.outputs["otbm"] = str(otbm_path)

                # Report file
                report_json_path = self.output_dir / "report.json"
                report_data = {
                    "prompt": prompt,
                    "timestamp": timestamp,
                    "intent": report.stats.get("intent", {}),
                    "themes": report.stats.get("themes", []),
                    "hunt": report.stats.get("hunt", {}),
                    "spawns": report.stats.get("spawns", {}),
                    "lua": report.stats.get("lua", {}),
                    "validation": report.stats.get("validation", {}),
                    "success": len(report.errors) == 0,
                    "errors": report.errors,
                    "warnings": report.warnings,
                }
                with open(report_json_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                report.outputs["report"] = str(report_json_path)
                print(f"       -> {report_json_path}")

                # ASCII preview text
                from core.preview.preview_generator import PreviewGenerator
                pg = PreviewGenerator(tile_size=8)
                ascii_preview = pg.generate_ascii(hunt_area)
                ascii_path = self.output_dir / "preview_ascii.txt"
                with open(ascii_path, "w", encoding="utf-8") as f:
                    f.write(ascii_preview)
                report.outputs["ascii_preview"] = str(ascii_path)
                print(f"       -> {ascii_path}")

                if preview_path:
                    report.outputs["preview_png"] = str(preview_path)

                report.success = len(report.errors) == 0

            # -- Final summary --
            print(f"\n{'='*60}")
            print(f"  PIPELINE COMPLETADO")
            print(f"  Exito: {'SI' if report.success else 'NO'}")
            print(f"  Errores: {len(report.errors)}")
            print(f"  Warnings: {len(report.warnings)}")
            print(f"  Archivos generados: {len(report.outputs)}")
            for key, path in report.outputs.items():
                print(f"    - {key}: {path}")
            print(f"{'='*60}\n")

            # Show ASCII preview
            if ascii_preview:
                print(ascii_preview)

        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {e}"
            report.errors.append(error_msg)
            report.success = False
            print(f"\n  [ERROR]: {error_msg}")
            traceback.print_exc()

        return report

    # -- City Branch Stages --

    def _stage3city_generate_city(self, intent, theme_data):
        """Generate a City model using the city generator."""
        from core.generators.city.city_generator import CityGenerator

        style = intent.theme[0] if intent.theme else "issavi"
        level_range = tuple(intent.level_range)

        generator = CityGenerator(
            style=style,
            min_level=level_range[0],
            max_level=level_range[1],
        )
        return generator.city

    def _stage4city_convert(self, city_model):
        """Convert City model to WorldModel for OTBM export."""
        from core.generators.city.city_to_worldmodel import CityToWorldModel
        from core.generators.city.city_generator import CityGenerator

        # Get the template used by the generator
        generator = CityGenerator(style=city_model.theme)
        converter = CityToWorldModel(city_model, generator.template)
        return converter.convert()

    def _stage5city_otbm(self, world_model, intent, timestamp: str) -> Optional[str]:
        """Export a city WorldModel directly to OTBM."""
        try:
            from core.otbm.otbm_serializer import OtbmSerializer
            from core.otbm.otbm_validator import OtbmValidator

            serializer = OtbmSerializer()
            otbm_bytes = serializer.serialize(world_model)

            validator = OtbmValidator()
            val_report = validator.validate(otbm_bytes)
            if val_report.status == "failure":
                print(f"       [WARN] OTBM validation: {val_report.errors}")
            if val_report.warnings:
                for w in val_report.warnings:
                    print(f"       [WARN] OTBM: {w}")

            name = "_".join(intent.theme) if intent.theme else "city"
            otbm_path = self.output_dir / f"{name}.otbm"
            otbm_path.write_bytes(otbm_bytes)

            self._generate_city_templates(world_model, name)

            print(f"       OTBM valid: {'SI' if val_report.is_valid else 'NO'} "
                  f"({val_report.stats.get('tiles', 0)} tiles, "
                  f"{val_report.stats.get('towns', 0)} towns, "
                  f"{val_report.stats.get('waypoints', 0)} waypoints, "
                  f"{len(otbm_bytes)} bytes)")
            return otbm_path
        except Exception as e:
            print(f"       [ERROR] City OTBM export failed: {e}")
            return None

    @staticmethod
    def _generate_city_templates(world_model, base_name: str) -> None:
        """Generate companion XML files for a city export."""
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # House XML
        houses = getattr(world_model, "cities", []) or []
        if houses:
            house_lines = ["<houses>"]
            for i, h in enumerate(houses, start=1):
                house_lines.append(
                    f'  <house name="House{i}">\n'
                    f'    <location x="{h.get("x", 0)}" y="{h.get("y", 0)}" z="{h.get("z", 7)}" />\n'
                    f'  </house>'
                )
            house_lines.append("</houses>")
            (output_dir / f"{base_name}.house.xml").write_text(
                "\n".join(house_lines) + "\n", encoding="utf-8"
            )

        # Monster XML (city spawns)
        spawns = getattr(world_model, "spawns", []) or []
        monsters = set()
        for s in spawns:
            n = s.get("monster") or s.get("name") or ""
            if n:
                monsters.add(str(n))
        if monsters:
            monster_lines = ["<monsters>"]
            for m in sorted(monsters):
                monster_lines.append(f'  <monster name="{m}" respawn="60" />')
            monster_lines.append("</monsters>")
            (output_dir / f"{base_name}.monster.xml").write_text(
                "\n".join(monster_lines) + "\n", encoding="utf-8"
            )

        # Zone XML
        tiles = list(getattr(world_model, "tiles", {}).values())
        if tiles:
            xs = [getattr(t, "x", 0) for t in tiles]
            ys = [getattr(t, "y", 0) for t in tiles]
            zs = [getattr(t, "z", 0) for t in tiles]
            zone_xml = f"""<zones>
  <zone id="1" name="{base_name}">
    <area x1="{min(xs)}" y1="{min(ys)}"
          x2="{max(xs)}" y2="{max(ys)}"
          z="{min(zs)}" />
  </zone>
</zones>
"""
            (output_dir / f"{base_name}.zones.xml").write_text(zone_xml, encoding="utf-8")
    # -- Dungeon Branch Stages --

    def _stage3dungeon_generate(self, intent, theme_data):
        """Generate a multi-floor Dungeon model."""
        from core.generators.dungeon.dungeon_generator import DungeonGenerator

        style = intent.theme[0] if intent.theme else "issavi"
        level_range = tuple(intent.level_range)

        generator = DungeonGenerator(
            style=style,
            min_level=level_range[0],
            max_level=level_range[1],
        )
        return generator.dungeon

    def _stage4dungeon_convert(self, dungeon_model):
        """Convert Dungeon model to WorldModel for OTBM export."""
        from core.generators.dungeon.dungeon_to_worldmodel import DungeonToWorldModel

        converter = DungeonToWorldModel(dungeon_model)
        return converter.convert()

    def _stage5dungeon_otbm(self, world_model, intent, dungeon_model, timestamp: str) -> Optional[str]:
        """Export a multi-floor dungeon WorldModel to OTBM."""
        try:
            from core.otbm.otbm_serializer import OtbmSerializer
            from core.otbm.otbm_validator import OtbmValidator

            serializer = OtbmSerializer()
            otbm_bytes = serializer.serialize(world_model)

            validator = OtbmValidator()
            val_report = validator.validate(otbm_bytes)
            if val_report.status == "failure":
                print(f"       [WARN] OTBM validation: {val_report.errors}")
            if val_report.warnings:
                for w in val_report.warnings:
                    print(f"       [WARN] OTBM: {w}")

            name = "_".join(intent.theme) if intent.theme else "dungeon"
            otbm_path = self.output_dir / f"{name}.otbm"
            otbm_path.write_bytes(otbm_bytes)

            self._generate_dungeon_templates(dungeon_model, world_model, name)

            floors = len(set(getattr(t, "z", 7) for t in world_model.tiles.values()))
            print(f"       OTBM valid: {'SI' if val_report.is_valid else 'NO'} "
                  f"({val_report.stats.get('tiles', 0)} tiles, "
                  f"{floors} floors, "
                  f"{val_report.stats.get('monsters', 0)} monsters, "
                  f"{len(otbm_bytes)} bytes)")
            return otbm_path
        except Exception as e:
            print(f"       [ERROR] Dungeon OTBM export failed: {e}")
            return None

    @staticmethod
    def _generate_dungeon_templates(dungeon_model, world_model, base_name: str) -> None:
        """Generate companion XML files for a dungeon export."""
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Monster XML
        monsters = set()
        for s in getattr(dungeon_model, "spawns", []) or []:
            n = s.get("monster") or s.get("name") or ""
            if n:
                monsters.add(str(n))
        if monsters:
            monster_lines = ["<monsters>"]
            for m in sorted(monsters):
                monster_lines.append(f'  <monster name="{m}" respawn="60" />')
            monster_lines.append("</monsters>")
            (output_dir / f"{base_name}.monster.xml").write_text(
                "\n".join(monster_lines) + "\n", encoding="utf-8"
            )

        # Zone XML (multi-floor)
        tiles = list(getattr(world_model, "tiles", {}).values())
        if tiles:
            xs = [getattr(t, "x", 0) for t in tiles]
            ys = [getattr(t, "y", 0) for t in tiles]
            zs = [getattr(t, "z", 0) for t in tiles]
            zone_xml = f"""<zones>
  <zone id="1" name="{base_name}">
    <area x1="{min(xs)}" y1="{min(ys)}"
          x2="{max(xs)}" y2="{max(ys)}"
          z="{min(zs)}" />
  </zone>
</zones>
"""
            (output_dir / f"{base_name}.zones.xml").write_text(zone_xml, encoding="utf-8")

    # -- Stage Implementations --

    def _stage1_interpret(self, prompt: str):
        from core.prompt_interpreter import PromptInterpreter
        interpreter = PromptInterpreter()
        return interpreter.interpret(prompt)

    def _stage2_resolve_themes(self, intent):
        from core.themes.theme_resolver import ThemeResolver
        resolver = ThemeResolver()
        themes = resolver.resolve_all(intent.theme)
        return themes

    def _stage3_generate_hunt(self, intent, theme_data):
        from core.generators.hunt_generator import HuntGenerator
        from core.themes.theme_resolver import ThemeResolver

        resolver = ThemeResolver()
        merged = resolver.merge_themes(theme_data)

        level_range = tuple(intent.level_range)
        avg_level = (level_range[0] + level_range[1]) / 2

        # Scale map size based on level range
        if avg_level < 200:
            w, h = 25, 25
            rooms = 3
            boss = False
        elif avg_level < 400:
            w, h = 35, 35
            rooms = 4
            boss = True
        else:
            w, h = 45, 45
            rooms = 5
            boss = True

        generator = HuntGenerator(seed=42)
        from core.world import WorldModel
        world = WorldModel()
        theme_name = intent.theme[0] if intent.theme else "issavi"
        context = {
            "theme": theme_name,
            "level_min": level_range[0],
            "level_max": level_range[1],
            "density": "medium",
            "width": w,
            "height": h,
            "z": 7,
        }
        return generator.generate(world, context)

    def _stage4_generate_spawns(self, hunt_area, theme_data, intent):
        from core.spawn.spawn_generator import SpawnGenerator
        from core.themes.theme_resolver import ThemeResolver

        resolver = ThemeResolver()
        merged = resolver.merge_themes(theme_data)

        generator = SpawnGenerator()
        return generator.generate(
            hunt_area.rooms,
            merged.monsters,
            tuple(intent.level_range),
            hunt_area.base_z,
        )

    def _stage5_generate_lua(self, hunt_area, spawn_plan, intent):
        from core.lua.lua_generator import LuaGenerator

        generator = LuaGenerator()
        name = "+".join(intent.theme) if intent.theme else "generated_map"
        return generator.generate(hunt_area, spawn_plan, name)

    def _stage6_validate(self, lua_script):
        from core.compiler.lua_validator import LuaValidator
        from validators.qa_pipeline import QAPipeline

        validator = LuaValidator()
        result = validator.validate(lua_script.code)

        # QA Pipeline: RME Validator + Asset Validator + Monster Validator + Tile Validator
        qa = QAPipeline()
        qa_report = qa.run(lua_script.code)

        if qa_report["status"] == "failure":
            # Bloquear output si el QA pipeline falla
            from dataclasses import dataclass, field

            @dataclass
            class WrappedError:
                line: int = 0
                message: str = ""
                severity: str = "error"

            @dataclass
            class WrappedReport:
                is_valid: bool = False
                errors: list = field(default_factory=list)
                warnings: list = field(default_factory=list)
                stats: dict = field(default_factory=dict)

            wrapped = WrappedReport(
                is_valid=False,
                stats={"qa_pipeline": qa_report},
            )
            for err in qa_report["errors"]:
                wrapped.errors.append(WrappedError(line=0, message=err, severity="error"))
            return wrapped

        # Wrap ValidationResult to provide .is_valid and .stats
        from dataclasses import dataclass, field

        @dataclass
        class WrappedReport:
            is_valid: bool = True
            errors: list = field(default_factory=list)
            warnings: list = field(default_factory=list)
            stats: dict = field(default_factory=dict)

        @dataclass
        class WrappedError:
            line: int = 0
            message: str = ""
            severity: str = "error"

        wrapped = WrappedReport(
            is_valid=(result.status == "success"),
            stats={
                "total_lines": len(lua_script.code.split('\n')),
                "tiles_created": lua_script.tile_count,
                "spawns_set": lua_script.spawn_count,
                "creatures_set": lua_script.creature_count,
                "items_added": lua_script.tile_count + lua_script.spawn_count,
                "borders_placed": lua_script.border_count,
                "qa_pipeline": qa_report,
            }
        )

        for err in result.errors:
            wrapped.errors.append(WrappedError(line=0, message=err, severity="error"))

        for warn in result.warnings:
            wrapped.warnings.append(WrappedError(line=0, message=warn, severity="warning"))

        return wrapped

    def _stage7_preview(self, hunt_area, intent, timestamp: str) -> Optional[str]:
        from core.preview.preview_generator import PreviewGenerator

        name = "_".join(intent.theme) if intent.theme else "map"
        png_path = self.output_dir / "preview.png"

        pg = PreviewGenerator(tile_size=10)
        result = pg.generate_png(hunt_area, str(png_path))
        return result

    def _stage8_export_otbm(self, hunt_area, spawn_plan, intent, timestamp: str) -> Optional[str]:
        """
        Export hunt area + spawn plan as a real .otbm file.

        Uses the OTBM serializer with NodeEncoder for native OTBM output.
        """
        try:
            from core.otbm.otbm_serializer import OtbmSerializer
            from core.otbm.otbm_validator import OtbmValidator

            # Serialize hunt area to OTBM
            serializer = OtbmSerializer()
            otbm_bytes = serializer.serialize_hunt_area(hunt_area, spawn_plan)

            # Validate
            validator = OtbmValidator()
            val_report = validator.validate(otbm_bytes)
            if val_report.status == "failure":
                print(f"       [WARN] OTBM validation: {val_report.errors}")
            if val_report.warnings:
                for w in val_report.warnings:
                    print(f"       [WARN] OTBM: {w}")

            # Write file
            name = "_".join(intent.theme) if intent.theme else "hunt"
            otbm_path = self.output_dir / f"{name}.otbm"
            otbm_path.write_bytes(otbm_bytes)

            # Generate companion templates (monsters XML)
            self._generate_otbm_templates(hunt_area, spawn_plan, intent, name)

            print(f"       OTBM valid: {'SI' if val_report.is_valid else 'NO'} "
                  f"({val_report.stats.get('tiles', 0)} tiles, "
                  f"{val_report.stats.get('monsters', 0)} monsters, "
                  f"{len(otbm_bytes)} bytes)")
            return otbm_path
        except ImportError as e:
            print(f"       [WARN] OTBM module not available: {e}")
            return None
        except Exception as e:
            print(f"       [ERROR] OTBM export failed: {e}")
            return None

    @staticmethod
    def _generate_otbm_templates(hunt_area, spawn_plan, intent, base_name: str) -> None:
        """Generate companion XML files for the OTBM export."""
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Monster XML
        monsters = set()
        for s in getattr(hunt_area, "spawns", []) or []:
            if len(s) >= 3:
                monsters.add(s[2])
        if spawn_plan:
            for entry in getattr(spawn_plan, "spawns", []):
                monsters.add(entry.monster_name)
            boss = getattr(spawn_plan, "boss_spawn", None)
            if boss:
                monsters.add(boss.monster_name)

        if monsters:
            monster_lines = ["<monsters>"]
            for m in sorted(monsters):
                monster_lines.append(f'  <monster name="{m}" respawn="60" />')
            monster_lines.append("</monsters>")
            (output_dir / f"{base_name}.monster.xml").write_text(
                "\n".join(monster_lines) + "\n", encoding="utf-8"
            )

        # Zone XML
        zone_xml = f"""<zones>
  <zone id="1" name="{base_name}">
    <area x1="{hunt_area.base_x}" y1="{hunt_area.base_y}"
          x2="{hunt_area.base_x + hunt_area.width}"
          y2="{hunt_area.base_y + hunt_area.height}"
          z="{hunt_area.base_z}" />
  </zone>
</zones>
"""
        (output_dir / f"{base_name}.zones.xml").write_text(zone_xml, encoding="utf-8")


# -- CLI Entry Point --

def main():
    runner = PipelineRunner()

    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Genera una zona Issavi + Roshamuul nivel 300-500"
        print(f"Modo demo. Prompt: {prompt}")

    report = runner.run(prompt)

    if report.success:
        print("\nMVP V0.1 pipeline completado exitosamente.")
        sys.exit(0)
    else:
        print("\nPipeline completado con errores.")
        sys.exit(1)


if __name__ == "__main__":
    main()