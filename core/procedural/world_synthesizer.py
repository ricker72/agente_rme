"""
HITO 16 - Procedural World Generation: World Synthesizer
=========================================================

The final assembly step: takes the intermediate output of the
ContinentGenerator (biome tiles, terrain features, roads, rivers,
structures, spawns, regions) and produces a clean, validated,
fully-populated `WorldModel` ready for export / preview / playtest.

The synthesizer can:
    - merge multiple partial WorldModels into one
    - normalize chunk keys
    - attach default AIArchitect / BlueprintRegistry metadata
    - produce a complete `WorldModel` that satisfies the WorldValidator

Architecture:
    [intermediate result] -> WorldSynthesizer.synthesize(...) -> WorldModel
    (or)                  -> WorldSynthesizer.merge(worlds)       -> WorldModel

Public API:
    WorldSynthesizer
    SynthesisReport
    synthesize(plan_or_result, ...)         -> WorldModel
    merge(*worlds)                          -> WorldModel
    validate_synthesis(world)               -> WorldValidationResult
    attach_ai_architect(world, architect)   -> None
    attach_blueprint_registry(world, reg)   -> None
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from core.world import (
    WorldModel, Tile, Item, Spawn, Structure, Region, Chunk,
    WorldValidator, WorldValidationResult,
)

from .continent_generator import (
    ContinentGenerator, ContinentResult, generate_continent,
)
from .biome_generator import BiomeGenerator
from .terrain_generator import TerrainGenerator
from .road_generator import RoadGenerator
from .river_generator import RiverGenerator

logger = logging.getLogger(__name__)


# =============================================================================
# SynthesisReport
# =============================================================================

@dataclass
class SynthesisReport:
    """Summary of a synthesis pass."""
    world: WorldModel
    total_tiles: int = 0
    total_structures: int = 0
    total_spawns: int = 0
    total_regions: int = 0
    total_chunks: int = 0
    themes_used: List[str] = field(default_factory=list)
    ai_architect_attached: bool = False
    blueprint_registry_attached: bool = False
    validation: Optional[WorldValidationResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tiles": self.total_tiles,
            "total_structures": self.total_structures,
            "total_spawns": self.total_spawns,
            "total_regions": self.total_regions,
            "total_chunks": self.total_chunks,
            "themes_used": self.themes_used,
            "ai_architect_attached": self.ai_architect_attached,
            "blueprint_registry_attached": self.blueprint_registry_attached,
            "validation": self.validation.summary() if self.validation else None,
            "metadata": dict(self.metadata),
        }


# =============================================================================
# WorldSynthesizer
# =============================================================================

class WorldSynthesizer:
    """
    The final step of HITO 16.

    Takes a `ContinentResult` (or a `WorldPlan`) and produces a clean,
    validated `WorldModel` with chunking, metadata, and the AI
    architect's metadata if attached.

    Usage:
        synthesizer = WorldSynthesizer(seed=42)
        world = synthesizer.synthesize(plan)
        report = synthesizer.last_report
        print(report.to_dict())
    """

    def __init__(
        self,
        continent_generator: Optional[ContinentGenerator] = None,
        validator: Optional[WorldValidator] = None,
        seed: Optional[int] = None,
        auto_validate: bool = True,
    ) -> None:
        self._seed = int(seed) if seed is not None else random.randint(0, 999999)
        self._continent = continent_generator or ContinentGenerator(seed=self._seed)
        self._validator = validator or WorldValidator()
        self._auto_validate = auto_validate
        self.last_report: Optional[SynthesisReport] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesize(
        self,
        plan_or_result: Any,
        ai_architect: Optional[Any] = None,
        blueprint_registry: Optional[Any] = None,
        theme_resolver: Optional[Any] = None,
    ) -> WorldModel:
        """
        Build a world from a plan or merge a ContinentResult.

        If `plan_or_result` is a `ContinentResult` (has `.world`), we
        run the synthesis on that world. Otherwise we treat it as a
        WorldPlan and run the ContinentGenerator first.
        """
        if self._looks_like_result(plan_or_result):
            result: ContinentResult = plan_or_result
            world = result.world
        else:
            # Plan: run continent generator
            world = self._continent.generate(plan_or_result)
            result = ContinentResult(
                world=world,
                zones_placed=self._extract_zones_from_plan(plan_or_result),
                metadata={
                    "seed": self._seed,
                    "prompt": _plan_attr(plan_or_result, "prompt", default=""),
                    "primary_theme": _plan_attr(plan_or_result, "primary_theme",
                                                default="generic"),
                },
            )

        # Normalize the world
        world = self._normalize(world)

        # Run validation
        validation: Optional[WorldValidationResult] = None
        if self._auto_validate:
            validation = self._validator.validate(world)

        # Build the report
        themes = list(result.metadata.get("themes_resolved", []) or [])
        if not themes:
            # Fall back to the plan's themes or the primary theme
            themes = list(
                _plan_attr(plan_or_result, "themes", default=[]) or []
            ) or [_plan_attr(plan_or_result, "primary_theme", default="generic")]
        report = SynthesisReport(
            world=world,
            total_tiles=world.tile_count(),
            total_structures=world.structure_count(),
            total_spawns=sum(
                1 for t in world.tiles.values() if t.spawn is not None
            ),
            total_regions=world.region_count(),
            total_chunks=world.chunk_count(),
            themes_used=themes,
            validation=validation,
            metadata=dict(result.metadata),
        )

        if ai_architect is not None:
            self.attach_ai_architect(world, ai_architect)
            report.ai_architect_attached = True
        if blueprint_registry is not None:
            self.attach_blueprint_registry(world, blueprint_registry)
            report.blueprint_registry_attached = True

        # Re-run validation in case attachments added anything
        if ai_architect is not None or blueprint_registry is not None:
            if self._auto_validate:
                report.validation = self._validator.validate(world)

        self.last_report = report
        return world

    def merge(
        self,
        worlds: Sequence[WorldModel],
        ai_architect: Optional[Any] = None,
        blueprint_registry: Optional[Any] = None,
    ) -> WorldModel:
        """Merge multiple WorldModels into one."""
        if not worlds:
            return WorldModel()
        if len(worlds) == 1:
            return self._normalize(worlds[0])

        target = WorldModel()
        for w in worlds:
            self._copy_into(w, target)

        target = self._normalize(target)

        report = SynthesisReport(
            world=target,
            total_tiles=target.tile_count(),
            total_structures=target.structure_count(),
            total_spawns=sum(
                1 for t in target.tiles.values() if t.spawn is not None
            ),
            total_regions=target.region_count(),
            total_chunks=target.chunk_count(),
            metadata={"merged_from": len(worlds)},
        )
        if ai_architect is not None:
            self.attach_ai_architect(target, ai_architect)
            report.ai_architect_attached = True
        if blueprint_registry is not None:
            self.attach_blueprint_registry(target, blueprint_registry)
            report.blueprint_registry_attached = True
        if self._auto_validate:
            report.validation = self._validator.validate(target)
        self.last_report = report
        return target

    def validate_synthesis(self, world: WorldModel) -> WorldValidationResult:
        """Run the WorldValidator on a synthesized world."""
        return self._validator.validate(world)

    def attach_ai_architect(self, world: WorldModel, architect: Any) -> None:
        """
        Attach an AIArchitect reference to the world model so downstream
        consumers can find the planner that produced it.
        """
        # We store it as a custom attribute (not part of the schema).
        setattr(world, "_ai_architect", architect)
        setattr(world, "_synthesis_source", "ai_architect")

    def attach_blueprint_registry(
        self, world: WorldModel, registry: Any,
    ) -> None:
        """Attach a BlueprintRegistry reference to the world model."""
        setattr(world, "_blueprint_registry", registry)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _looks_like_result(self, obj: Any) -> bool:
        return (
            obj is not None
            and hasattr(obj, "world")
            and hasattr(obj, "zones_placed")
        )

    def _extract_zones_from_plan(self, plan: Any) -> List[Dict[str, Any]]:
        layout = _plan_attr(plan, "layout")
        if layout is None:
            return []
        raw = _plan_attr(layout, "zones", "placed_zones", default=[]) or []
        out: List[Dict[str, Any]] = []
        for z in raw:
            if isinstance(z, dict):
                out.append(dict(z))
            else:
                out.append({
                    "x": getattr(z, "x", 0),
                    "y": getattr(z, "y", 0),
                    "z": getattr(z, "z", 7),
                    "width": getattr(z, "width", 40),
                    "height": getattr(z, "height", 40),
                    "name": getattr(z, "name", "zone"),
                    "theme": getattr(z, "theme", "generic"),
                    "zone_kind": getattr(z, "zone_kind", "hunt"),
                })
        return out

    def _normalize(self, world: WorldModel) -> WorldModel:
        """
        Normalize the world: drop duplicate tiles, clamp coords, and
        refresh chunks.
        """
        # Clamp all coordinates
        for key, tile in list(world.tiles.items()):
            if tile.x < 0 or tile.y < 0:
                world.remove_tile(tile.x, tile.y, tile.z)
            elif tile.z < 0 or tile.z > 15:
                world.remove_tile(tile.x, tile.y, tile.z)
        return world

    def _copy_into(self, src: WorldModel, dst: WorldModel) -> None:
        """Copy all data from src into dst (dst wins on conflict)."""
        for tile in src.tiles.values():
            dst.set_tile(tile)
        for s in src.structures:
            dst.add_structure(s)
        for r in src.regions:
            dst.add_region(r)


# =============================================================================
# Helpers
# =============================================================================

def _plan_attr(plan: Any, *names: str, default: Any = None) -> Any:
    if plan is None:
        return default
    if isinstance(plan, dict):
        for n in names:
            if n in plan:
                return plan[n]
        return default
    for n in names:
        v = getattr(plan, n, None)
        if v is not None:
            return v
    return default


# =============================================================================
# Module-level helpers
# =============================================================================

def synthesize(
    plan_or_result: Any,
    seed: Optional[int] = None,
    ai_architect: Optional[Any] = None,
    blueprint_registry: Optional[Any] = None,
    auto_validate: bool = True,
) -> WorldModel:
    """One-shot helper: build and return a synthesized WorldModel."""
    synth = WorldSynthesizer(seed=seed, auto_validate=auto_validate)
    return synth.synthesize(
        plan_or_result,
        ai_architect=ai_architect,
        blueprint_registry=blueprint_registry,
    )


def merge(*worlds: WorldModel) -> WorldModel:
    """One-shot helper: merge multiple WorldModels into one."""
    synth = WorldSynthesizer()
    return synth.merge(list(worlds))


def validate_synthesis(world: WorldModel) -> WorldValidationResult:
    """One-shot helper: validate a synthesized world."""
    return WorldValidator().validate(world)


def attach_ai_architect(world: WorldModel, architect: Any) -> None:
    """One-shot helper: attach AIArchitect to a world."""
    WorldSynthesizer().attach_ai_architect(world, architect)


def attach_blueprint_registry(world: WorldModel, registry: Any) -> None:
    """One-shot helper: attach BlueprintRegistry to a world."""
    WorldSynthesizer().attach_blueprint_registry(world, registry)
