"""MERGE-07A semantic Ground Brush Engine.

Brushes produce deterministic edit proposals. Workspace services validate and
commit those proposals through an adapter, then mark localized dirty regions.
Rendering remains outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Protocol, Tuple


Coord = Tuple[int, int, int]
ChunkCoord = Tuple[int, int, int]


class BrushType(Enum):
    """Brush families accepted by the editor."""

    GROUND = "ground"
    TERRAIN = "terrain"
    ITEM = "item"
    ERASE = "erase"


class BrushShape(Enum):
    """Deterministic ground brush footprint shapes."""

    SQUARE = "square"
    CIRCLE = "circle"


@dataclass(frozen=True)
class MaterialDefinition:
    """Semantic material selected from the material palette."""

    material_id: str
    name: str
    ground_item_id: int
    tileset: str = ""
    source: str = "BrushDatabase"


@dataclass(frozen=True)
class BrushDefinition:
    """Semantic brush entry used for editing, never raw appearance metadata."""

    brush_id: str
    name: str
    brush_type: BrushType
    material: MaterialDefinition
    source: str = "BrushDatabase"
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, order=True)
class TileState:
    """Minimal tile state used by tests and validation."""

    x: int
    y: int
    z: int
    ground_id: Optional[int] = None
    brush_id: str = ""


@dataclass(frozen=True, order=True)
class TileMutation:
    """A validated proposal for one ground replacement."""

    x: int
    y: int
    z: int
    ground_id: int
    brush_id: str
    material_id: str


@dataclass(frozen=True)
class DirtyRegion:
    """Localized dirty region covering affected ground tiles."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int
    z: int

    @classmethod
    def from_coords(cls, coords: Iterable[Coord]) -> "DirtyRegion":
        ordered = sorted(set(coords))
        if not ordered:
            raise ValueError("DirtyRegion requires at least one coordinate")
        xs = [coord[0] for coord in ordered]
        ys = [coord[1] for coord in ordered]
        z_values = {coord[2] for coord in ordered}
        if len(z_values) != 1:
            raise ValueError("DirtyRegion requires a single floor")
        return cls(min(xs), min(ys), max(xs), max(ys), ordered[0][2])

    @classmethod
    def from_mutations(cls, mutations: Iterable[TileMutation]) -> "DirtyRegion":
        return cls.from_coords((m.x, m.y, m.z) for m in mutations)

    def expand(self, amount: int = 0) -> "DirtyRegion":
        return DirtyRegion(
            self.min_x - amount,
            self.min_y - amount,
            self.max_x + amount,
            self.max_y + amount,
            self.z,
        )


@dataclass(frozen=True)
class GroundBrushDiagnostics:
    """Diagnostics emitted by preview and commit flows."""

    events: Tuple[str, ...] = ()
    messages: Tuple[str, ...] = ()

    def with_event(self, event: str, message: str = "") -> "GroundBrushDiagnostics":
        return GroundBrushDiagnostics(
            events=self.events + (event,),
            messages=self.messages + ((message,) if message else ()),
        )


@dataclass(frozen=True)
class GroundBrushFootprint:
    """Deterministic affected coordinate set."""

    coords: Tuple[Coord, ...]
    bounds: DirtyRegion
    size: int
    shape: BrushShape


@dataclass(frozen=True)
class GroundBrushRequest:
    """Ground brush operation request."""

    brush_definition: BrushDefinition
    material_definition: MaterialDefinition
    center_coord: Coord
    floor: int
    size: int = 1
    shape: BrushShape = BrushShape.SQUARE


@dataclass(frozen=True)
class GroundBrushPreview:
    """Non-mutating preview response."""

    brush_definition: BrushDefinition
    material_definition: MaterialDefinition
    center_coord: Coord
    floor: int
    size: int
    shape: BrushShape
    coords: Tuple[Coord, ...]
    bounds: DirtyRegion
    valid: bool
    diagnostics: GroundBrushDiagnostics
    affected_chunks: Tuple[ChunkCoord, ...]
    autoborder_pending: bool = True


@dataclass(frozen=True)
class GroundBrushResult:
    """Commit response from workspace services."""

    brush_definition: BrushDefinition
    material_definition: MaterialDefinition
    center_coord: Coord
    floor: int
    size: int
    shape: BrushShape
    coords: Tuple[Coord, ...]
    bounds: DirtyRegion
    valid: bool
    applied: bool
    diagnostics: GroundBrushDiagnostics
    affected_chunks: Tuple[ChunkCoord, ...]
    autoborder_pending: bool = True


@dataclass(frozen=True)
class EditorAction:
    """Compatibility proposal used by existing MAP-01 tests."""

    name: str
    brush: BrushDefinition
    mutations: Tuple[TileMutation, ...]
    dirty_region: DirtyRegion
    preview: bool = False


@dataclass
class DirtyRegionManager:
    """Localized dirty-region collector."""

    regions: List[DirtyRegion] = field(default_factory=list)

    def mark(self, region: DirtyRegion) -> None:
        self.regions.append(region)


@dataclass
class RenderQueue:
    """Render-queue boundary; it records dirty jobs only."""

    queued_regions: List[DirtyRegion] = field(default_factory=list)

    def enqueue(self, region: DirtyRegion) -> None:
        self.queued_regions.append(region)


class CertifiedCoreAdapter(Protocol):
    """Adapter boundary for all ground mutations."""

    def paint_ground(
        self,
        coords: Tuple[Coord, ...],
        material: MaterialDefinition,
        z: int,
        options: Optional[Dict[str, object]] = None,
    ) -> GroundBrushResult:
        ...


def _chunk_coords(coords: Iterable[Coord], chunk_size: int = 16) -> Tuple[ChunkCoord, ...]:
    return tuple(
        sorted({(x // chunk_size, y // chunk_size, z) for x, y, z in coords})
    )


class MappingEngineCoreAdapter:
    """Adapter over OpenTibiaMappingEngine for MERGE-07A ground edits."""

    def __init__(self, mapping_engine: object) -> None:
        self.mapping_engine = mapping_engine
        self.last_paint_ground: Optional[Tuple[Tuple[Coord, ...], MaterialDefinition, int, Dict[str, object]]] = None

    def paint_ground(
        self,
        coords: Tuple[Coord, ...],
        material: MaterialDefinition,
        z: int,
        options: Optional[Dict[str, object]] = None,
    ) -> GroundBrushResult:
        options = dict(options or {})
        diagnostics = GroundBrushDiagnostics(("ground_commit_requested",), ())
        self.last_paint_ground = (coords, material, z, options)
        if not coords:
            return self._result(coords, material, z, options, False, False, diagnostics.with_event("ground_commit_rejected", "empty footprint"))
        if material.ground_item_id < 0:
            return self._result(coords, material, z, options, False, False, diagnostics.with_event("ground_commit_rejected", "invalid ground material"))
        if any(coord_z != z for _x, _y, coord_z in coords):
            return self._result(coords, material, z, options, False, False, diagnostics.with_event("ground_commit_rejected", "mixed floors"))
        if any(x < 0 or y < 0 or not 0 <= coord_z <= 15 for x, y, coord_z in coords):
            return self._result(coords, material, z, options, False, False, diagnostics.with_event("ground_commit_rejected", "coordinate out of bounds"))
        if self._has_locked_tile(coords):
            return self._result(coords, material, z, options, False, False, diagnostics.with_event("ground_commit_rejected", "protected or locked tile"))

        brush_definition = options.get("brush_definition")
        official_command = getattr(brush_definition, "metadata", {}).get(
            "workspace_core_material", False
        )
        apply_official = getattr(self.mapping_engine, "apply_official_brush", None)
        if official_command and callable(apply_official):
            apply_official(material.name, coords)
            diagnostics = diagnostics.with_event("workspace_core_material_applied")
            diagnostics = diagnostics.with_event("autoborder_applied")
            return self._result(
                coords,
                material,
                z,
                options,
                True,
                True,
                diagnostics.with_event("ground_commit_applied"),
            )

        mutations = tuple(
            TileMutation(
                x=x,
                y=y,
                z=coord_z,
                ground_id=material.ground_item_id,
                brush_id=str(options.get("brush_id", "")),
                material_id=material.material_id,
            )
            for x, y, coord_z in coords
        )
        self.mapping_engine.set_ground_tiles(mutations)
        diagnostics = diagnostics.with_event("ground_commit_validated")
        diagnostics = diagnostics.with_event("ground_tiles_changed", str(len(coords)))
        diagnostics = diagnostics.with_event("autoborder_pending", "autoborder pending")
        return self._result(coords, material, z, options, True, True, diagnostics.with_event("ground_commit_applied"))

    def validate_ground_mutations(self, mutations: Tuple[TileMutation, ...]) -> bool:
        return all(
            mutation.x >= 0 and mutation.y >= 0 and 0 <= mutation.z <= 15
            for mutation in mutations
        )

    def apply_ground_mutations(self, mutations: Tuple[TileMutation, ...]) -> object:
        return self.mapping_engine.set_ground_tiles(mutations)

    def _has_locked_tile(self, coords: Tuple[Coord, ...]) -> bool:
        tiles = getattr(self.mapping_engine, "tiles", {})
        for coord in coords:
            tile = tiles.get(coord)
            metadata = dict(getattr(tile, "metadata", {}) or {}) if tile is not None else {}
            if metadata.get("locked") or metadata.get("protected"):
                return True
        return False

    def _result(
        self,
        coords: Tuple[Coord, ...],
        material: MaterialDefinition,
        z: int,
        options: Dict[str, object],
        valid: bool,
        applied: bool,
        diagnostics: GroundBrushDiagnostics,
    ) -> GroundBrushResult:
        bounds = DirtyRegion.from_coords(coords) if coords else DirtyRegion(0, 0, 0, 0, z)
        brush_definition = options.get(
            "brush_definition",
            BrushDefinition(
                brush_id=str(options.get("brush_id", "")),
                name=material.name,
                brush_type=BrushType.GROUND,
                material=material,
                source=material.source,
            ),
        )
        return GroundBrushResult(
            brush_definition=brush_definition,
            material_definition=material,
            center_coord=options.get("center_coord", coords[0] if coords else (0, 0, z)),
            floor=z,
            size=int(options.get("size", 1)),
            shape=options.get("shape", BrushShape.SQUARE),
            coords=coords,
            bounds=bounds,
            valid=valid,
            applied=applied,
            diagnostics=diagnostics,
            affected_chunks=_chunk_coords(coords),
        )


class WorkspaceServices:
    """Validation, mutation, dirty-region, and render-queue boundary."""

    def __init__(
        self,
        core_adapter: CertifiedCoreAdapter,
        dirty_regions: Optional[DirtyRegionManager] = None,
        render_queue: Optional[RenderQueue] = None,
    ) -> None:
        self.core_adapter = core_adapter
        self.dirty_regions = dirty_regions or DirtyRegionManager()
        self.render_queue = render_queue or RenderQueue()
        self.last_result: Optional[GroundBrushResult] = None

    def paint_ground(
        self,
        request: GroundBrushRequest,
        footprint: GroundBrushFootprint,
    ) -> GroundBrushResult:
        result = self.core_adapter.paint_ground(
            footprint.coords,
            request.material_definition,
            request.floor,
            {
                "brush_id": request.brush_definition.brush_id,
                "brush_definition": request.brush_definition,
                "center_coord": request.center_coord,
                "size": request.size,
                "shape": request.shape,
            },
        )
        if result.applied:
            self.dirty_regions.mark(result.bounds)
            self.render_queue.enqueue(result.bounds)
            result = GroundBrushResult(
                brush_definition=result.brush_definition,
                material_definition=result.material_definition,
                center_coord=result.center_coord,
                floor=result.floor,
                size=result.size,
                shape=result.shape,
                coords=result.coords,
                bounds=result.bounds,
                valid=result.valid,
                applied=result.applied,
                diagnostics=result.diagnostics.with_event("dirty_chunks", str(result.affected_chunks)),
                affected_chunks=result.affected_chunks,
                autoborder_pending=result.autoborder_pending,
            )
        self.last_result = result
        return result

    def commit(self, action: EditorAction) -> bool:
        if action.preview:
            return False
        request = GroundBrushRequest(
            brush_definition=action.brush,
            material_definition=action.brush.material,
            center_coord=(action.mutations[0].x, action.mutations[0].y, action.mutations[0].z),
            floor=action.mutations[0].z,
            size=1,
            shape=BrushShape.SQUARE,
        )
        footprint = GroundBrushFootprint(
            coords=tuple((m.x, m.y, m.z) for m in action.mutations),
            bounds=action.dirty_region,
            size=1,
            shape=BrushShape.SQUARE,
        )
        return self.paint_ground(request, footprint).applied


class GroundBrushEngine:
    """Deterministic RME-style ground brush behavior."""

    def create_footprint(
        self,
        center_coord: Coord,
        size: int = 1,
        shape: BrushShape = BrushShape.SQUARE,
    ) -> GroundBrushFootprint:
        x, y, z = center_coord
        radius = max(0, int(size) - 1)
        coords: set[Coord] = set()
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if shape == BrushShape.CIRCLE and dx * dx + dy * dy > radius * radius:
                    continue
                coords.add((x + dx, y + dy, z))
        ordered = tuple(sorted(coords))
        return GroundBrushFootprint(
            coords=ordered,
            bounds=DirtyRegion.from_coords(ordered),
            size=max(1, int(size)),
            shape=shape,
        )

    def create_preview(self, request: GroundBrushRequest) -> GroundBrushPreview:
        self._require_ground_brush(request.brush_definition)
        footprint = self.create_footprint(
            request.center_coord,
            request.size,
            request.shape,
        )
        valid, diagnostics = self.validate(request, footprint)
        diagnostics = diagnostics.with_event("ground_preview_created")
        diagnostics = diagnostics.with_event("autoborder_pending", "autoborder pending")
        return GroundBrushPreview(
            brush_definition=request.brush_definition,
            material_definition=request.material_definition,
            center_coord=request.center_coord,
            floor=request.floor,
            size=request.size,
            shape=request.shape,
            coords=footprint.coords,
            bounds=footprint.bounds,
            valid=valid,
            diagnostics=diagnostics,
            affected_chunks=_chunk_coords(footprint.coords),
        )

    def validate(
        self,
        request: GroundBrushRequest,
        footprint: Optional[GroundBrushFootprint] = None,
    ) -> Tuple[bool, GroundBrushDiagnostics]:
        self._require_ground_brush(request.brush_definition)
        diagnostics = GroundBrushDiagnostics()
        if request.material_definition.ground_item_id < 0:
            return False, diagnostics.with_event("ground_commit_rejected", "invalid ground material")
        footprint = footprint or self.create_footprint(
            request.center_coord, request.size, request.shape
        )
        if any(x < 0 or y < 0 or not 0 <= z <= 15 for x, y, z in footprint.coords):
            return False, diagnostics.with_event("ground_commit_rejected", "coordinate out of bounds")
        if any(z != request.floor for _x, _y, z in footprint.coords):
            return False, diagnostics.with_event("ground_commit_rejected", "coordinate floor mismatch")
        return True, diagnostics.with_event("ground_commit_validated")

    def commit(
        self,
        services: WorkspaceServices,
        brush: BrushDefinition,
        center: Coord,
        size: int = 1,
        shape: BrushShape = BrushShape.SQUARE,
    ) -> bool:
        request = GroundBrushRequest(
            brush_definition=brush,
            material_definition=brush.material,
            center_coord=center,
            floor=center[2],
            size=max(1, int(size)),
            shape=shape,
        )
        footprint = self.create_footprint(center, request.size, shape)
        valid, diagnostics = self.validate(request, footprint)
        if not valid:
            services.last_result = GroundBrushResult(
                brush_definition=brush,
                material_definition=brush.material,
                center_coord=center,
                floor=center[2],
                size=request.size,
                shape=shape,
                coords=footprint.coords,
                bounds=footprint.bounds,
                valid=False,
                applied=False,
                diagnostics=diagnostics,
                affected_chunks=_chunk_coords(footprint.coords),
            )
            return False
        result = services.paint_ground(request, footprint)
        return result.applied

    def commit_coords(
        self,
        services: WorkspaceServices,
        brush: BrushDefinition,
        coords: Iterable[Coord],
    ) -> bool:
        """Commit an arbitrary visual gesture as one validated editor action."""
        self._require_ground_brush(brush)
        ordered = tuple(sorted(set(coords)))
        if not ordered:
            return False
        floors = {coord[2] for coord in ordered}
        if len(floors) != 1:
            raise ValueError("Ground brush batch requires a single floor")
        floor = ordered[0][2]
        footprint = GroundBrushFootprint(
            coords=ordered,
            bounds=DirtyRegion.from_coords(ordered),
            size=1,
            shape=BrushShape.SQUARE,
        )
        request = GroundBrushRequest(
            brush_definition=brush,
            material_definition=brush.material,
            center_coord=ordered[0],
            floor=floor,
            size=1,
            shape=BrushShape.SQUARE,
        )
        valid, diagnostics = self.validate(request, footprint)
        if not valid:
            services.last_result = GroundBrushResult(
                brush_definition=brush,
                material_definition=brush.material,
                center_coord=ordered[0],
                floor=floor,
                size=1,
                shape=BrushShape.SQUARE,
                coords=ordered,
                bounds=footprint.bounds,
                valid=False,
                applied=False,
                diagnostics=diagnostics,
                affected_chunks=_chunk_coords(ordered),
            )
            return False
        return services.paint_ground(request, footprint).applied

    def cancel_preview(self) -> GroundBrushDiagnostics:
        return GroundBrushDiagnostics(("ground_preview_cancelled",), ())

    def footprint(
        self,
        center: Coord,
        size: int = 1,
        shape: BrushShape = BrushShape.SQUARE,
    ) -> Tuple[Coord, ...]:
        return self.create_footprint(center, size, shape).coords

    def propose(
        self,
        brush: BrushDefinition,
        center: Coord,
        size: int = 1,
        shape: BrushShape = BrushShape.SQUARE,
        preview: bool = True,
    ) -> EditorAction:
        self._require_ground_brush(brush)
        footprint = self.create_footprint(center, size, shape)
        mutations = tuple(
            TileMutation(
                x=x,
                y=y,
                z=z,
                ground_id=brush.material.ground_item_id,
                brush_id=brush.brush_id,
                material_id=brush.material.material_id,
            )
            for x, y, z in footprint.coords
        )
        return EditorAction(
            name="Ground Brush",
            brush=brush,
            mutations=mutations,
            dirty_region=footprint.bounds,
            preview=preview,
        )

    def preview(
        self,
        brush: BrushDefinition,
        center: Coord,
        size: int = 1,
        shape: BrushShape = BrushShape.SQUARE,
    ) -> EditorAction:
        return self.propose(brush, center, size=size, shape=shape, preview=True)

    def _require_ground_brush(self, brush: object) -> None:
        if not isinstance(brush, BrushDefinition):
            raise TypeError("GroundBrushEngine requires BrushDefinition, not raw appearance metadata")
        if brush.brush_type not in {BrushType.GROUND, BrushType.TERRAIN}:
            raise ValueError("GroundBrushEngine only accepts ground brush definitions")
