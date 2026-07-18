"""
MAP-01D / MERGE-07A brush behavior.

The legacy ``BrushManager`` remains for MAP-01 tests. MERGE-07A adds a
semantic ground brush engine that produces deterministic edit proposals before
any workspace mutation happens.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from dataclasses import dataclass

from workspace_core.editor.ground_brush_engine import (
    BrushDefinition as BrushDefinition,
    BrushShape as BrushShape,
    BrushType as BrushType,
    DirtyRegion as DirtyRegion,
    DirtyRegionManager as DirtyRegionManager,
    EditorAction as EditorAction,
    GroundBrushDiagnostics as GroundBrushDiagnostics,
    GroundBrushEngine as GroundBrushEngine,
    GroundBrushFootprint as GroundBrushFootprint,
    GroundBrushPreview as GroundBrushPreview,
    GroundBrushRequest as GroundBrushRequest,
    GroundBrushResult as GroundBrushResult,
    MappingEngineCoreAdapter as MappingEngineCoreAdapter,
    MaterialDefinition as MaterialDefinition,
    RenderQueue as RenderQueue,
    TileMutation as TileMutation,
    TileState as TileState,
    WorkspaceServices as WorkspaceServices,
)

__all__ = [
    "BrushDefinition",
    "BrushShape",
    "BrushType",
    "DirtyRegion",
    "DirtyRegionManager",
    "EditorAction",
    "GroundBrushDiagnostics",
    "GroundBrushEngine",
    "GroundBrushFootprint",
    "GroundBrushPreview",
    "GroundBrushRequest",
    "GroundBrushResult",
    "MappingEngineCoreAdapter",
    "MaterialDefinition",
    "RenderQueue",
    "TileMutation",
    "TileState",
    "WorkspaceServices",
]

DEFAULT_TERRAIN_ID = 0
DEFAULT_ITEM_ID = 2148
VALID_TERRAIN_IDS = {0, 1, 2, 3, 4, 5}
VALID_ITEM_IDS = {2148, 2152, 2160, 1987, 1988}


def extend_valid_item_ids(item_ids) -> None:
    """Extend the editor allowlist with official OpenTibia item ids."""
    VALID_ITEM_IDS.update(int(item_id) for item_id in item_ids if int(item_id) >= 0)


def is_valid_terrain(terrain_id: int) -> bool:
    """Return whether a terrain id is allowed for MAP-01 NECRO editing."""
    return terrain_id in VALID_TERRAIN_IDS


def is_valid_item(item_id: int) -> bool:
    """Return whether an item id is allowed for MAP-01 NECRO editing."""
    return item_id in VALID_ITEM_IDS


@dataclass
class Brush:
    """Brush configuration"""
    brush_type: BrushType
    radius: int = 1
    terrain_id: Optional[int] = None
    item_id: Optional[int] = None

    def is_valid(self) -> bool:
        """Check if brush is properly configured"""
        if self.brush_type == BrushType.TERRAIN:
            return self.terrain_id is not None and self.terrain_id >= 0
        elif self.brush_type == BrushType.ITEM:
            return self.item_id is not None and self.item_id >= 0
        elif self.brush_type == BrushType.ERASE:
            return True
        return False

class BrushManager:
    """Brush management for NECRO mapping"""

    # MAP-01 uses a deliberately small OpenTibia allowlist until real OTB data is wired in.
    VALID_TERRAIN_IDS = VALID_TERRAIN_IDS
    VALID_ITEM_IDS = VALID_ITEM_IDS

    def __init__(self):
        self.current_brush: Optional[Brush] = None
        self.brush_preview_active = False
        self.preview_x: Optional[int] = None
        self.preview_y: Optional[int] = None
        self.preview_z: int = 7

    def set_terrain_brush(self, terrain_id: int, radius: int = 1) -> bool:
        """Set terrain brush"""
        if terrain_id in self.VALID_TERRAIN_IDS:
            self.current_brush = Brush(
                brush_type=BrushType.TERRAIN,
                radius=radius,
                terrain_id=terrain_id
            )
            return True
        return False

    def set_item_brush(self, item_id: int, radius: int = 1) -> bool:
        """Set item brush"""
        if item_id in self.VALID_ITEM_IDS:
            self.current_brush = Brush(
                brush_type=BrushType.ITEM,
                radius=radius,
                item_id=item_id
            )
            return True
        return False

    def set_erase_brush(self, radius: int = 1):
        """Set erase brush"""
        self.current_brush = Brush(
            brush_type=BrushType.ERASE,
            radius=radius
        )

    def clear_brush(self):
        """Clear current brush"""
        self.current_brush = None
        self._clear_preview()

    def _clear_preview(self):
        """Clear brush preview"""
        self.brush_preview_active = False
        self.preview_x = None
        self.preview_y = None

    def update_preview(self, x: int, y: int, z: int = 7):
        """Update brush preview position"""
        if self.current_brush:
            self.brush_preview_active = True
            self.preview_x = x
            self.preview_y = y
            self.preview_z = z

    def get_preview_tiles(self) -> List[Tuple[int, int, int]]:
        """Get tiles that would be affected by brush at preview position"""
        if not self.current_brush or not self.brush_preview_active:
            return []

        if self.preview_x is None or self.preview_y is None:
            return []

        tiles = []
        radius = max(1, self.current_brush.radius)
        span = range(-(radius - 1), radius)

        for dx in span:
            for dy in span:
                x = self.preview_x + dx
                y = self.preview_y + dy
                tiles.append((x, y, self.preview_z))

        return tiles

    def apply_brush(self, workspace, x: int, y: int, z: int = 7) -> bool:
        """Apply current brush to workspace"""
        if not self.current_brush or not self.current_brush.is_valid():
            return False

        if not workspace or not workspace.project:
            return False

        applied = False
        radius = max(1, self.current_brush.radius)
        span = range(-(radius - 1), radius)

        for dx in span:
            for dy in span:
                tile_x = x + dx
                tile_y = y + dy

                if self.current_brush.brush_type == BrushType.TERRAIN:
                    workspace.set_ground_id(tile_x, tile_y, z, self.current_brush.terrain_id)
                    applied = True
                elif self.current_brush.brush_type == BrushType.ITEM:
                    workspace.add_item(tile_x, tile_y, z, self.current_brush.item_id)
                    applied = True
                elif self.current_brush.brush_type == BrushType.ERASE:
                    # For erase, we remove all items from tile
                    tile = workspace.get_tile(tile_x, tile_y, z)
                    if tile and tile.items:
                        for item_id in tile.items[:]:  # Copy to avoid modification during iteration
                            workspace.remove_item(tile_x, tile_y, z, item_id)
                        applied = True

        return applied

    def get_brush_info(self) -> dict:
        """Get information about current brush"""
        if not self.current_brush:
            return {
                'active': False,
                'type': None,
                'radius': 0,
                'terrain_id': None,
                'item_id': None
            }

        return {
            'active': True,
            'type': self.current_brush.brush_type.value,
            'radius': self.current_brush.radius,
            'terrain_id': self.current_brush.terrain_id,
            'item_id': self.current_brush.item_id,
            'valid': self.current_brush.is_valid(),
            'preview_active': self.brush_preview_active,
            'preview_position': (self.preview_x, self.preview_y, self.preview_z) if self.preview_x is not None and self.preview_y is not None else None
        }
