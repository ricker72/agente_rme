from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.world_generator.gameplay_runtime_materializer import (
    GameplayRuntimeMaterializer,
    RuntimeSpawn,
    RuntimeZone,
    runtime_definitions_from_necro,
)
from core.world_generator.mapper_planner import (
    MapperPlan,
    MapperPlannedRegion,
    MapperPlannedRoute,
    mapper_plan_to_color_blueprint,
)
from core.world_generator.hierarchical_architectural_planner import HierarchicalArchitecturalPlanner
from core.world_generator.contextual_material_resolver import ContextualMaterialResolver
from core.world_generator.mapping_detail_critic import MappingDetailCritic
from core.world_generator.otbm_world.model import OtbmItem, OtbmTile, OtbmWorldModel
from core.world_generator.otbm_world.serializer import serialize_world
from core.world_generator.rme_brush_engine import RMEBrushEngine
from core.world_generator.rme_materials_necro_v5 import classify_items, load_material_catalog
from core.world_generator.semantic_color_blueprint import BlueprintMaterializer, SemanticColorPalette
from core.world_generator.wall_brush_visual_footprint import WallBrushVisualFootprintModel
from core.world_generator.wall_alignment_certifier import WallAlignmentCertifier
from core.world_generator.planner_memory_critic import PlannerMemoryConformanceCritic
from core.editor.mapping_engine import WorkspaceMappingEngine
from core.world_generator.planner_database_client import PlannerDatabaseClient
from core.world_generator.experience_learning_loop import ExperienceLearningLoop
from core.world_generator.ecological_distribution_planner import EcologicalDistributionPlanner
from core.world_generator.repetition_critic import RepetitionCritic


def generate_color_first_map(
    plan: MapperPlan,
    *,
    root: str | Path = ".",
    asset_root: str | Path | None = None,
    output_name: str = "generated_color.otbm",
    footprints: dict[str, list[list[int]]] | None = None,
    entity_plan: dict[str, Any] | None = None,
    hunt_blueprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a map and persist its complete QA experience for later learning."""
    base = Path(root).resolve()
    try:
        learning: Any = PlannerDatabaseClient(base)
    except (OSError, RuntimeError, ValueError):
        learning = ExperienceLearningLoop.for_root(base)
    guidance = learning.guidance(plan.objective)
    if "experience_learning" not in plan.reference_style:
        plan.reference_style["experience_learning"] = guidance
        plan.policies["learned_positive_rule_count"] = len(guidance.get("positive_rules", ()))
        plan.policies["learned_negative_constraint_count"] = len(guidance.get("negative_constraints", ()))
    experience_id = learning.start_experience(
        plan.objective,
        planner_snapshot=plan.to_report(),
        context={
            "output_name": Path(output_name).name,
            "runtime_requested": footprints is not None and entity_plan is not None and hunt_blueprint is not None,
            "pipeline": "color_first_map_pipeline",
        },
    )
    try:
        report = _generate_color_first_map_impl(
            plan,
            root=base,
            asset_root=asset_root,
            output_name=output_name,
            footprints=footprints,
            entity_plan=entity_plan,
            hunt_blueprint=hunt_blueprint,
        )
        learning.attach_artifact(experience_id, report["output"])
        learning_report = _record_generation_experience(learning, experience_id, report, base)
        report["experience_learning"] = learning_report
        report_path = base / "exports" / "COLOR_FIRST_MAP_REPORT.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    except Exception as exc:
        learning.mark_failed(experience_id, exc)
        raise


def _generate_color_first_map_impl(
    plan: MapperPlan,
    *,
    root: str | Path = ".",
    asset_root: str | Path | None = None,
    output_name: str = "generated_color.otbm",
    footprints: dict[str, list[list[int]]] | None = None,
    entity_plan: dict[str, Any] | None = None,
    hunt_blueprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = Path(root)
    assets = Path(asset_root) if asset_root is not None else base
    classification = classify_items(load_material_catalog(assets))
    brush_engine = RMEBrushEngine.load(assets, classification)
    palette = (
        SemanticColorPalette.official_defaults()
        .apply_planner_material_intents(plan)
        .bind_rme_brush_engine(brush_engine)
    )
    hierarchical_audit = HierarchicalArchitecturalPlanner(base).enrich(plan)
    blueprint = mapper_plan_to_color_blueprint(plan, name="necro-color-first")
    contextual_audit = ContextualMaterialResolver().resolve(blueprint, plan)
    ecological_audit = EcologicalDistributionPlanner().apply(
        blueprint,
        plan,
        available_tokens=palette.tokens,
    )
    repetition_audit = RepetitionCritic().repair(blueprint, plan)
    detail_qa = MappingDetailCritic().evaluate(blueprint)
    if len(blueprint.positions) >= 10_000 and detail_qa["status"] != "PASS":
        raise ValueError(f"Mapping detail QA failed: {detail_qa['checks']}")
    memory_conformance = PlannerMemoryConformanceCritic().evaluate(
        blueprint,
        plan.reference_style.get("visual_memory", {}),
    )
    if memory_conformance["status"] != "PASS":
        raise ValueError("Planner visual-memory conformance failed")
    masks_dir = base / "exports" / "color_blueprint"
    mask_paths = blueprint.export_color_masks(masks_dir, palette)

    editor = WorkspaceMappingEngine(base)
    materialization = BlueprintMaterializer(palette, brush_engine).materialize(blueprint, editor)
    if len(blueprint.positions) >= 10_000 and materialization.border_item_count <= 0:
        raise ValueError("RME AutoBorder produced no serialized border items")
    sea_border = brush_engine.borders.get(5)
    sea_border_items = set(sea_border.edges.values()) if sea_border else set()
    sea_autoborder_present = bool(sea_border_items.intersection(materialization.border_item_ids))
    if len(blueprint.positions) >= 10_000 and not sea_autoborder_present:
        raise ValueError("Official sea GroundBrush border 5 was not serialized")
    wall_alignment = WallAlignmentCertifier().certify(blueprint, editor, palette, brush_engine)
    if wall_alignment["status"] != "PASS":
        raise ValueError(
            f"RME wall alignment certification failed: {wall_alignment['mismatch_count']} mismatches"
        )
    output = base / "exports" / Path(output_name).name
    model = _editor_to_model(
        editor,
        plan,
        sidecar_stem=output.stem,
        protection_zone_tiles=blueprint.metadata.get("protection_zone_tiles", ()),
    )
    runtime_report: dict[str, Any] = {"status": "NOT_REQUESTED"}
    runtime_result = None
    if footprints is not None and entity_plan is not None and hunt_blueprint is not None:
        houses, spawns, zones = runtime_definitions_from_necro(
            footprints,
            entity_plan,
            hunt_blueprint,
        )
        runtime_result = GameplayRuntimeMaterializer().materialize(
            model,
            houses=houses,
            spawns=spawns,
            zones=zones,
            connection_routes=_connection_routes(plan),
        )
        model = runtime_result.model
        runtime_report = runtime_result.report
    elif blueprint.metadata.get("protection_zone_tiles"):
        spawns, zones = _runtime_definitions_from_compact_plan(plan, blueprint.metadata)
        runtime_result = GameplayRuntimeMaterializer().materialize(
            model,
            spawns=spawns,
            zones=zones,
        )
        model = runtime_result.model
        runtime_report = runtime_result.report

    binary, _tree = serialize_world(model)
    output.write_bytes(binary)
    if runtime_result is not None:
        runtime_result.write_sidecars(output.parent, output.stem)
    else:
        _write_empty_rme_sidecars(output)
    report = {
        "stage": "Planner Color Blueprint SharpMap-style Materialization",
        "status": "PASS",
        "flow": [
            "mapper_plan",
            "hierarchical_architectural_planner",
            "layered_rme_mapcolor_masks",
            "contextual_material_resolver",
            "ecological_distribution_planner",
            "density_budget",
            "repetition_critic_repair",
            "semantic_color_compositor",
            "official_rme_brush_resolution",
            "sprite_backed_tile_materialization",
            "otbm_serialization",
        ],
        "output": str(output),
        "output_bytes": len(binary),
        "hierarchical_architecture": hierarchical_audit,
        "contextual_material_resolution": contextual_audit,
        "ecological_distribution": ecological_audit,
        "repetition_critic": repetition_audit,
        "mapping_detail_qa": detail_qa,
        "blueprint": {
            "bounds": blueprint.bounds,
            "positions": len(blueprint.positions),
            "layers": {layer.name: len(mask.cells) for layer, mask in blueprint.layers.items()},
        },
        "palette": palette.audit(),
        "wall_visual_footprints": WallBrushVisualFootprintModel.load(assets).audit(
            brush_engine,
            {
                token.brush_name
                for token in palette.tokens.values()
                if token.layer.name in {"WALL", "DOOR_WINDOW"} and token.brush_name
            },
        ),
        "wall_alignment": wall_alignment,
        "world_reference_evidence": blueprint.metadata.get("reference_style", {}),
        "memory_conformance": memory_conformance,
        "materialization": asdict(materialization),
        "sea_ground_brush": {
            "brush": "sea",
            "ground_ids": [item.item_id for item in brush_engine.ground_brushes["sea"].items],
            "outer_border_ids": list(brush_engine.ground_brushes["sea"].outer_border_ids),
            "border_5_serialized": sea_autoborder_present,
        },
        "runtime": runtime_report,
        "masks": [str(path) for path in mask_paths],
    }
    report_path = base / "exports" / "COLOR_FIRST_MAP_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _runtime_definitions_from_compact_plan(
    plan: MapperPlan,
    metadata: dict[str, Any],
) -> tuple[tuple[RuntimeSpawn, ...], tuple[RuntimeZone, ...]]:
    """Materialize compact gameplay without inventing raw item IDs."""
    pz_tiles = tuple(
        (int(position[0]), int(position[1]), int(position[2]))
        for position in metadata.get("protection_zone_tiles", ())
        if len(position) == 3
    )
    zones = (RuntimeZone(1, "Protection Zone", pz_tiles, 0x0001),)
    if plan.policies.get("compact_objective_kind") != "krailos_island":
        return (), zones

    cx, cy, z = (int(value) for value in plan.policies.get("city_center", (1000, 1000, 7)))
    # Creature families and relative density are learned from the z7 Krailos
    # spawn profile; coordinates are original to this generated island.
    placements = (
        ("Ogre Brute", -27, -12),
        ("Clomp", -20, -24),
        ("Ogre Shaman", -31, 8),
        ("Ogre Savage", -20, 20),
        ("Ogre Brute", -10, 22),
        ("Clomp", 12, 26),
        ("Ogre Shaman", 27, 15),
        ("Ogre Savage", 31, -4),
        ("Ogre Brute", 21, -18),
        ("Clomp", 8, -28),
        ("Ogre Shaman", -10, -27),
        ("Ogre Savage", -34, -3),
    )
    spawns = tuple(
        RuntimeSpawn(name, (cx + dx, cy + dy, z), 3, 90, "monster")
        for name, dx, dy in placements
    )
    return spawns, zones


def _record_generation_experience(
    learning: Any,
    experience_id: str,
    report: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    """Translate pipeline evidence into canonical promotion gates."""
    detail = report.get("mapping_detail_qa", {})
    memory = report.get("memory_conformance", {})
    wall = report.get("wall_alignment", {})
    sea = report.get("sea_ground_brush", {})
    visual_pass = all(
        (
            detail.get("status") == "PASS",
            memory.get("status") == "PASS",
            wall.get("status") == "PASS",
            bool(sea.get("border_5_serialized")),
        )
    )
    learning.record_qa(experience_id, "mapping_detail", str(detail.get("status", "MISSING")), evidence=detail)
    learning.record_qa(experience_id, "memory_conformance", str(memory.get("status", "MISSING")), evidence=memory)
    learning.record_qa(experience_id, "wall_alignment", str(wall.get("status", "MISSING")), evidence=wall)
    learning.record_qa(
        experience_id,
        "visual_qa",
        "PASS" if visual_pass else "FAIL",
        evidence={
            "mapping_detail": detail.get("status"),
            "memory_conformance": memory.get("status"),
            "wall_alignment": wall.get("status"),
            "official_sea_autoborder": bool(sea.get("border_5_serialized")),
        },
        score=1.0 if visual_pass else 0.0,
    )
    output = Path(report["output"])
    try:
        from core.editor.otbm_corpus_roundtrip import OTBMCorpusRoundtripCertifier

        roundtrip = OTBMCorpusRoundtripCertifier().certify((output,)).to_dict()
        learning.record_qa(
            experience_id,
            "otbm_roundtrip",
            roundtrip["status"],
            evidence=roundtrip,
            score=1.0 if roundtrip["status"] == "PASS" else 0.0,
        )
    except Exception as exc:  # QA failure is evidence; the generated artifact remains inspectable.
        learning.record_qa(
            experience_id,
            "otbm_roundtrip",
            "ERROR",
            evidence={"error": f"{type(exc).__name__}: {exc}"},
            score=0.0,
        )
    try:
        from core.editor.item_safety_certifier import OTBMItemSafetyCertifier

        safety = OTBMItemSafetyCertifier(root).certify(output).to_dict()
        learning.record_qa(
            experience_id,
            "material_safety",
            safety["status"],
            evidence=safety,
            score=1.0 if safety["status"] == "PASS" else 0.0,
        )
    except Exception as exc:
        learning.record_qa(
            experience_id,
            "material_safety",
            "ERROR",
            evidence={"error": f"{type(exc).__name__}: {exc}"},
            score=0.0,
        )
    runtime = report.get("runtime", {})
    runtime_status = str(runtime.get("status", "NOT_REQUESTED"))
    # An omitted runtime gate is pending evidence, not evidence of failure.
    # This keeps the experience awaiting validation instead of teaching a
    # negative rule merely because the caller requested visual generation only.
    if runtime_status != "NOT_REQUESTED":
        learning.record_qa(
            experience_id,
            "playability",
            "PASS" if runtime_status in {"PASS", "CERTIFIED"} else runtime_status,
            evidence=runtime,
            score=1.0 if runtime_status in {"PASS", "CERTIFIED"} else 0.0,
        )
    return learning.evaluate_promotion(experience_id)


def mapper_plan_from_report(report: dict[str, Any]) -> MapperPlan:
    plan = MapperPlan(
        objective=str(report["objective"]),
        policies=dict(report.get("policies", {})),
        reference_style=dict(report.get("reference_style", {})),
        architecture=dict(report.get("architecture", {})),
    )
    plan.regions.extend(
        MapperPlannedRegion(
            name=str(region["name"]),
            role=str(region["role"]),
            style=str(region["style"]),
            anchor=tuple(int(value) for value in region["anchor"]),
            radius=tuple(int(value) for value in region["radius"]),
            terrain=str(region["terrain"]),
            tags=tuple(str(tag) for tag in region.get("tags", ())),
        )
        for region in report.get("regions", ())
    )
    plan.routes.extend(
        MapperPlannedRoute(
            name=str(route["name"]),
            role=str(route["role"]),
            points=tuple(tuple(int(value) for value in point) for point in route["points"]),
            width=int(route["width"]),
            terrain=str(route["terrain"]),
            tags=tuple(str(tag) for tag in route.get("tags", ())),
        )
        for route in report.get("routes", ())
    )
    if not plan.regions or not plan.routes:
        raise ValueError("Mapper Planner report has no regions or routes")
    return plan


def generate_color_first_from_report(
    *,
    root: str | Path = ".",
    report_path: str | Path = "exports/MAPPER_PLANNER_REPORT.json",
    output_name: str = "generated_color.otbm",
) -> dict[str, Any]:
    base = Path(root)
    source = Path(report_path)
    if not source.is_absolute():
        source = base / source
    plan = mapper_plan_from_report(json.loads(source.read_text(encoding="utf-8")))
    if not plan.reference_style:
        style_path = base / "exports" / "WORLD_OTBM_PLANNER_STYLE_PROFILE_FULL.json"
        if style_path.is_file():
            plan.reference_style = json.loads(style_path.read_text(encoding="utf-8"))
    grammar_path = base / "exports" / "WORLD_OTBM_VISUAL_GRAMMAR.json"
    if grammar_path.is_file():
        plan.reference_style["visual_grammar"] = json.loads(grammar_path.read_text(encoding="utf-8"))
    composition_path = base / "exports" / "VISUAL_COMPOSITION_REFERENCE_PROFILE.json"
    if composition_path.is_file():
        plan.reference_style["composition_reference"] = json.loads(
            composition_path.read_text(encoding="utf-8")
        )
        plan.policies["visual_design_floors"] = list(range(0, 8))
        plan.policies["visual_reference_policy"] = (
            "composition metrics only; official appearances and RME brushes materialize every tile"
        )
    memory_path = base / "exports" / "planner_visual_memory" / "VISUAL_MEMORY_CACHE.json"
    if memory_path.is_file():
        memory = json.loads(memory_path.read_text(encoding="utf-8"))
        plan.reference_style["visual_memory"] = memory.get("learned_priors", {})
        plan.policies["visual_memory_reference_count"] = int(
            memory.get("learned_priors", {}).get("reference_count", 0)
        )
    return generate_color_first_map(plan, root=base, output_name=output_name)


def _editor_to_model(
    editor: WorkspaceMappingEngine,
    plan: MapperPlan,
    *,
    sidecar_stem: str,
    protection_zone_tiles: Any = (),
) -> OtbmWorldModel:
    tiles: list[OtbmTile] = []
    normalized_tiles = 0
    removed_replaced_grounds = 0
    catalog = editor.editor_map.item_catalog
    pz_tiles = {
        tuple(int(value) for value in position)
        for position in protection_zone_tiles
        if isinstance(position, (list, tuple)) and len(position) == 3
    }
    for (x, y, z), tile in sorted(editor.tiles.items()):
        if tile.ground_id is None:
            continue
        explicit_ground = int(tile.ground_id)
        source_stack = [explicit_ground, *(int(item_id) for item_id in tile.items if int(item_id) > 0)]
        explicit_type = catalog.get(explicit_ground)
        if explicit_type.is_border:
            raise ValueError(
                f"Transparent border item {explicit_ground} cannot own the ground slot at {(x, y, z)}"
            )
        if explicit_type.is_ground:
            # WorkspaceMappingEngine already owns a distinct ground slot. RME's
            # Tile::addItem replaces that slot when a second ground appears, so
            # serializing ground-flagged border pieces as ordinary items creates
            # transparent/black tiles. Keep the certified explicit ground and
            # discard accidental secondary grounds before writing OTBM.
            ground_id = explicit_ground
            item_ids = catalog.sort_items(
                item_id
                for item_id in source_stack[1:]
                if not catalog.get(item_id).is_ground
            )
        else:
            ground_id, item_ids = catalog.classify_stack(source_stack)
        if ground_id is None:
            continue
        canonical_stack = [ground_id, *item_ids]
        if canonical_stack != source_stack:
            normalized_tiles += 1
            removed_replaced_grounds += max(0, len(source_stack) - len(canonical_stack))
        items = [OtbmItem(int(ground_id), "ground", f"color-ground:{x}:{y}:{z}")]
        items.extend(
            OtbmItem(int(item_id), "item", f"color-item:{x}:{y}:{z}:{index}")
            for index, item_id in enumerate(item_ids)
        )
        attributes = {
            "tile_flags": 0x0001
        } if (x, y, z) in pz_tiles or tile.metadata.get("gameplay:spawn") == "true" else {}
        tiles.append(OtbmTile(x, y, z, tuple(items), attributes))
    map_width = max(2048, max((tile.x for tile in tiles), default=0) + 32)
    map_height = max(2048, max((tile.y for tile in tiles), default=0) + 32)
    return OtbmWorldModel(
        map_width,
        map_height,
        tuple(tiles),
        {
            "description": plan.objective,
            "spawn_monster_file": f"{sidecar_stem}-monster.xml",
            "spawn_npc_file": f"{sidecar_stem}-npc.xml",
            "house_file": f"{sidecar_stem}-house.xml",
            "zone_file": f"{sidecar_stem}-zones.xml",
            "color_first": True,
            "rme_stack_normalization": {
                "algorithm": "Canary Tile::addLoadedItem followed by Tile::update",
                "normalized_tiles": normalized_tiles,
                "removed_replaced_grounds": removed_replaced_grounds,
            },
        },
        ({
            "id": 1,
            "name": str(plan.policies.get("town_name", "AI Generated Area")),
            "temple": {
                "x": int(plan.policies.get("city_center", [1000, 1000, 7])[0]),
                "y": int(plan.policies.get("city_center", [1000, 1000, 7])[1]),
                "z": int(plan.policies.get("city_center", [1000, 1000, 7])[2]),
            },
        },),
    )


def _write_empty_rme_sidecars(output: Path) -> None:
    documents = {
        "house": "houses",
        "monster": "monsters",
        "npc": "npcs",
        "zones": "zones",
    }
    for suffix, root_name in documents.items():
        path = output.with_name(f"{output.stem}-{suffix}.xml")
        path.write_text(f'<?xml version="1.0"?>\n<{root_name} />\n', encoding="ascii")


def _connection_routes(plan: MapperPlan) -> tuple[tuple[tuple[int, int, int], ...], ...]:
    return tuple(
        tuple((int(x), int(y), 7) for x, y in route.points)
        for route in plan.routes
        if len(route.points) >= 2
    )
