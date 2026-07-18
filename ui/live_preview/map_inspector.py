"""
MAP-01E: NECRO Tile Inspector
Tile inspection functionality for OpenTibia mapping
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TileInspectionData:
    """Data structure for tile inspection"""
    x: int
    y: int
    z: int
    ground_id: int
    items: List[int]
    item_count: int
    has_spawn: bool = False
    has_waypoint: bool = False
    region_name: Optional[str] = None
    metadata: Dict = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for display"""
        return {
            'coordinates': (self.x, self.y, self.z),
            'ground_id': self.ground_id,
            'items': self.items,
            'item_count': self.item_count,
            'has_spawn': self.has_spawn,
            'has_waypoint': self.has_waypoint,
            'region_name': self.region_name,
            'metadata': self.metadata or {}
        }

class TileInspector:
    """Tile inspector for NECRO project"""

    def __init__(self):
        self.current_tile: Optional[TileInspectionData] = None
        self.editable_fields = ['metadata']  # Fields that can be edited

    def inspect_tile(self, workspace, x: int, y: int, z: int) -> Optional[TileInspectionData]:
        """Inspect tile at coordinates"""
        if not workspace or not workspace.project:
            return None

        tile = workspace.get_tile(x, y, z)
        if not tile:
            return None

        # Check if tile is in any region
        region_name = None
        for region in workspace.project.regions:
            if (region.min_x <= x <= region.max_x and
                region.min_y <= y <= region.max_y):
                region_name = region.name
                break

        # Check if tile has spawns
        has_spawn = any(
            spawn.x == x and spawn.y == y and spawn.z == z
            for spawn in workspace.project.spawns
        )

        # Check if tile has waypoints
        has_waypoint = any(
            wp.x == x and wp.y == y and wp.z == z
            for wp in workspace.project.waypoints
        )

        self.current_tile = TileInspectionData(
            x=x,
            y=y,
            z=z,
            ground_id=tile.ground_id,
            items=tile.items,
            item_count=len(tile.items),
            has_spawn=has_spawn,
            has_waypoint=has_waypoint,
            region_name=region_name,
            metadata=tile.metadata
        )

        return self.current_tile

    def get_current_inspection(self) -> Optional[Dict]:
        """Get current inspection data as dictionary"""
        if not self.current_tile:
            return None
        return self.current_tile.to_dict()

    def update_metadata(self, new_metadata: Dict) -> bool:
        """Update tile metadata"""
        if not self.current_tile:
            return False

        self.current_tile.metadata = new_metadata
        return True

    def can_edit_field(self, field_name: str) -> bool:
        """Check if field can be edited"""
        return field_name in self.editable_fields

    def get_editable_fields(self) -> List[str]:
        """Get list of editable fields"""
        return self.editable_fields

    def clear_inspection(self):
        """Clear current inspection"""
        self.current_tile = None

    def get_tile_summary(self) -> str:
        """Get human-readable summary of current tile"""
        if not self.current_tile:
            return "No tile selected"

        data = self.current_tile
        summary = f"Tile ({data.x}, {data.y}, {data.z})\n"
        summary += f"Ground: {data.ground_id}\n"
        summary += f"Items: {data.item_count}\n"

        if data.region_name:
            summary += f"Region: {data.region_name}\n"

        if data.has_spawn:
            summary += "Has spawn point\n"

        if data.has_waypoint:
            summary += "Has waypoint\n"

        if data.metadata:
            summary += f"Metadata: {len(data.metadata)} entries\n"

        return summary