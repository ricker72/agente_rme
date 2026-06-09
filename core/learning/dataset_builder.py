"""
Dataset Builder - Constructs datasets from OpenTibia maps for AI learning.

This module handles loading, parsing, and organizing map data into structured
datasets suitable for training machine learning models.
"""

import os
import json
import glob
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib


@dataclass
class MapMetadata:
    """Metadata extracted from a map file."""
    file_path: str
    file_hash: str
    file_size: int
    map_name: Optional[str]
    description: Optional[str]
    version: Optional[str]
    width: int
    height: int
    floors: int
    has_spawn: bool
    town_count: int
    house_count: int


@dataclass
class MapRegion:
    """A region within a map with specific characteristics."""
    region_id: str
    map_file: str
    x_start: int
    y_start: int
    z_start: int
    x_end: int
    y_end: int
    z_end: int
    region_type: str  # city, dungeon, cave, tower, temple, etc.
    style: Optional[str]  # issavi, roshamuul, soulwar, library, falcon, cobra
    features: Dict[str, Any]


@dataclass
class MapFeature:
    """A specific feature found in a map."""
    feature_id: str
    feature_type: str  # boss_room, temple, depot, shop, etc.
    location: Tuple[int, int, int]
    size: Tuple[int, int, int]
    properties: Dict[str, Any]
    connected_to: List[str]  # IDs of connected features


class DatasetBuilder:
    """Builds structured datasets from OpenTibia map files."""
    
    # Known map styles in OpenTibia
    KNOWN_STYLES = [
        "issavi", "roshamuul", "soulwar", "library", 
        "falcon", "cobra", "yalahar", "edron", "thais",
        "carlin", "venore", "ankrahmun", "darashia",
        "port_hope", "svargrond", "farmine", "gray_beach",
        "dreia", "krailos", "roshamuul", "feyrist"
    ]
    
    # Region type classifications
    REGION_TYPES = [
        "city", "dungeon", "cave", "tower", "temple",
        "depot", "arena", "quest_room", "boss_room",
        "house", "guildhall", "shop", "road", "bridge",
        "wall", "gate", "tunnel", "passage", "room",
        "corridor", "stairs", "ramp", "open_area", "forest",
        "mountain", "water", "swamp", "desert", "ice",
        "lava", "grass", "sand", "stone", "unknown"
    ]
    
    def __init__(self, maps_directory: str = None):
        """
        Initialize the dataset builder.
        
        Args:
            maps_directory: Directory containing map files (.otbm, .lua, .json)
        """
        self.maps_directory = maps_directory or "maps"
        self.maps_metadata: List[MapMetadata] = []
        self.regions: List[MapRegion] = []
        self.features: List[MapFeature] = []
        self.dataset: Dict[str, Any] = {}
        
    def scan_maps(self, directory: str = None) -> List[str]:
        """
        Scan directory for map files.
        
        Args:
            directory: Optional directory to scan (overrides default)
            
        Returns:
            List of map file paths
        """
        if directory is None:
            directory = self.maps_directory
            
        map_files = []
        extensions = ["*.otbm", "*.lua", "*.json", "*.xml"]
        
        for ext in extensions:
            pattern = os.path.join(directory, "**", ext)
            map_files.extend(glob.glob(pattern, recursive=True))
            
        return sorted(set(map_files))
    
    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def extract_metadata(self, file_path: str) -> Optional[MapMetadata]:
        """
        Extract metadata from a map file.
        
        Args:
            file_path: Path to the map file
            
        Returns:
            MapMetadata object or None if extraction fails
        """
        try:
            file_size = os.path.getsize(file_path)
            file_hash = self.compute_file_hash(file_path)
            
            # Parse based on file type
            if file_path.endswith('.json'):
                return self._parse_json_map(file_path, file_hash, file_size)
            elif file_path.endswith('.lua'):
                return self._parse_lua_map(file_path, file_hash, file_size)
            elif file_path.endswith('.otbm'):
                return self._parse_otbm_map(file_path, file_hash, file_size)
                
        except Exception as e:
            print(f"Error extracting metadata from {file_path}: {e}")
            
        return None
    
    def _parse_json_map(self, file_path: str, file_hash: str, 
                        file_size: int) -> MapMetadata:
        """Parse JSON format map file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        return MapMetadata(
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            map_name=data.get("name", data.get("map_name")),
            description=data.get("description"),
            version=data.get("version"),
            width=data.get("width", data.get("size", {}).get("width", 0)),
            height=data.get("height", data.get("size", {}).get("height", 0)),
            floors=data.get("floors", data.get("z_levels", 0)),
            has_spawn=data.get("has_spawn", False),
            town_count=len(data.get("towns", [])),
            house_count=len(data.get("houses", []))
        )
    
    def _parse_lua_map(self, file_path: str, file_hash: str,
                       file_size: int) -> MapMetadata:
        """Parse Lua format map file."""
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Extract basic info from Lua comments and structure
        name = None
        description = None
        
        for line in content.split('\n')[:50]:
            if '-- name:' in line.lower():
                name = line.split(':', 1)[1].strip()
            elif '-- description:' in line.lower():
                description = line.split(':', 1)[1].strip()
                
        # Estimate dimensions from map data
        width = 0
        height = 0
        floors = 0
        
        return MapMetadata(
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            map_name=name,
            description=description,
            version=None,
            width=width,
            height=height,
            floors=floors,
            has_spawn="spawn" in content.lower(),
            town_count=0,
            house_count=0
        )
    
    def _parse_otbm_map(self, file_path: str, file_hash: str,
                        file_size: int) -> MapMetadata:
        """Parse OTBM binary format map file."""
        # Basic OTBM header parsing
        # Full implementation would require binary parsing
        return MapMetadata(
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            map_name=os.path.basename(file_path),
            description=None,
            version=None,
            width=0,
            height=0,
            floors=0,
            has_spawn=False,
            town_count=0,
            house_count=0
        )
    
    def identify_region_type(self, region_data: Dict[str, Any]) -> str:
        """
        Identify the type of a region based on its characteristics.
        
        Args:
            region_data: Dictionary containing region properties
            
        Returns:
            Region type string
        """
        # Check for specific features
        features = region_data.get("features", [])
        tiles = region_data.get("tiles", [])
        
        # Count tile types
        ground_types = {}
        has_monsters = False
        has_npcs = False
        has_houses = False
        has_temple = False
        has_boss = False
        
        for tile in tiles:
            ground = tile.get("ground", "")
            ground_types[ground] = ground_types.get(ground, 0) + 1
            
            if tile.get("monster"):
                has_monsters = True
            if tile.get("npc"):
                has_npcs = True
            if tile.get("house"):
                has_houses = True
            if tile.get("temple"):
                has_temple = True
            if tile.get("boss"):
                has_boss = True
                
        # Determine region type based on characteristics
        if has_boss:
            return "boss_room"
        if has_temple:
            return "temple"
        if has_houses and has_npcs:
            return "city"
        if has_monsters and not has_npcs:
            return "dungeon"
        if "cave" in str(ground_types).lower():
            return "cave"
        if "tower" in str(features).lower():
            return "tower"
            
        # Default based on dominant ground type
        if ground_types:
            dominant = max(ground_types, key=ground_types.get)
            if "grass" in dominant:
                return "grass"
            elif "stone" in dominant:
                return "stone"
            elif "water" in dominant:
                return "water"
            elif "sand" in dominant:
                return "desert"
            elif "ice" in dominant:
                return "ice"
                
        return "unknown"
    
    def identify_style(self, region_data: Dict[str, Any]) -> Optional[str]:
        """
        Identify the architectural style of a region.
        
        Args:
            region_data: Dictionary containing region properties
            
        Returns:
            Style name or None if unknown
        """
        # Check for style indicators in name, description, or features
        name = region_data.get("name", "").lower()
        description = region_data.get("description", "").lower()
        features = region_data.get("features", [])
        
        text = f"{name} {description} {' '.join(features)}"
        
        for style in self.KNOWN_STYLES:
            if style.lower() in text:
                return style
                
        # Check for architectural patterns
        ground_types = region_data.get("ground_types", {})
        
        # Roshamuul style: dark, prison-like
        if any(t in ground_types for t in ["roshamuul_stone", "prison_wall"]):
            return "roshamuul"
            
        # Issavi style: desert, ancient
        if any(t in ground_types for t in ["sand", "ancient_stone", "issavi_tile"]):
            return "issavi"
            
        # Soul War style: soul-related themes
        if any(t in ground_types for t in ["soul_stone", "war_stone"]):
            return "soulwar"
            
        # Library style: bookshelves, study areas
        if "bookshelf" in str(features).lower() or "library_shelf" in ground_types:
            return "library"
            
        # Falcon style: bird motifs
        if "falcon" in text or any(t in ground_types for t in ["falcon_tile"]):
            return "falcon"
            
        # Cobra style: serpent motifs
        if "cobra" in text or any(t in ground_types for t in ["cobra_tile"]):
            return "cobra"
            
        return None
    
    def extract_regions(self, map_data: Dict[str, Any], 
                       file_path: str) -> List[MapRegion]:
        """
        Extract regions from map data.
        
        Args:
            map_data: Parsed map data
            file_path: Source file path
            
        Returns:
            List of MapRegion objects
        """
        regions = []
        region_id = 0
        
        # Process floor by floor
        floors = map_data.get("floors", [])
        for z, floor_data in enumerate(floors):
            # Segment floor into regions
            segments = self._segment_floor(floor_data, z)
            
            for segment in segments:
                region_id += 1
                region_type = self.identify_region_type(segment)
                style = self.identify_style(segment)
                
                region = MapRegion(
                    region_id=f"{file_path}_r{region_id}",
                    map_file=file_path,
                    x_start=segment.get("x_start", 0),
                    y_start=segment.get("y_start", 0),
                    z_start=segment.get("z", z),
                    x_end=segment.get("x_end", 0),
                    y_end=segment.get("y_end", 0),
                    z_end=segment.get("z", z),
                    region_type=region_type,
                    style=style,
                    features=segment.get("features", {})
                )
                regions.append(region)
                
        return regions
    
    def _segment_floor(self, floor_data: Dict[str, Any], 
                       z: int) -> List[Dict[str, Any]]:
        """
        Segment a floor into logical regions.
        
        This is a simplified implementation. A full implementation would
        use more sophisticated segmentation algorithms.
        """
        segments = []
        tiles = floor_data.get("tiles", [])
        
        if not tiles:
            return segments
            
        # Group tiles by proximity and similarity
        current_segment = {
            "x_start": float('inf'),
            "y_start": float('inf'),
            "x_end": 0,
            "y_end": 0,
            "z": z,
            "tiles": [],
            "features": {}
        }
        
        for tile in tiles:
            x = tile.get("x", 0)
            y = tile.get("y", 0)
            
            current_segment["x_start"] = min(current_segment["x_start"], x)
            current_segment["y_start"] = min(current_segment["y_start"], y)
            current_segment["x_end"] = max(current_segment["x_end"], x)
            current_segment["y_end"] = max(current_segment["y_end"], y)
            current_segment["tiles"].append(tile)
            
        if current_segment["tiles"]:
            segments.append(current_segment)
            
        return segments
    
    def build_dataset(self, output_path: str = None) -> Dict[str, Any]:
        """
        Build a complete dataset from all maps in the directory.
        
        Args:
            output_path: Optional path to save the dataset
            
        Returns:
            Complete dataset dictionary
        """
        map_files = self.scan_maps()
        print(f"Found {len(map_files)} map files")
        
        all_metadata = []
        all_regions = []
        all_features = []
        
        for map_file in map_files:
            print(f"Processing: {map_file}")
            
            # Extract metadata
            metadata = self.extract_metadata(map_file)
            if metadata:
                all_metadata.append(asdict(metadata))
                
            # Parse map and extract regions
            map_data = self._load_map_data(map_file)
            if map_data:
                regions = self.extract_regions(map_data, map_file)
                all_regions.extend([asdict(r) for r in regions])
                
        self.dataset = {
            "version": "1.0",
            "total_maps": len(all_metadata),
            "total_regions": len(all_regions),
            "metadata": all_metadata,
            "regions": all_regions,
            "features": [asdict(f) for f in all_features],
            "statistics": self._compute_statistics(all_metadata, all_regions)
        }
        
        if output_path:
            self.save_dataset(output_path)
            
        return self.dataset
    
    def _load_map_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load and parse map data from file."""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    return json.load(f)
            # Add more parsers as needed
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
        return None
    
    def _compute_statistics(self, metadata: List[Dict], 
                           regions: List[Dict]) -> Dict[str, Any]:
        """Compute dataset statistics."""
        style_counts = {}
        type_counts = {}
        
        for region in regions:
            style = region.get("style", "unknown")
            rtype = region.get("region_type", "unknown")
            
            style_counts[style] = style_counts.get(style, 0) + 1
            type_counts[rtype] = type_counts.get(rtype, 0) + 1
            
        return {
            "style_distribution": style_counts,
            "type_distribution": type_counts,
            "avg_map_size": sum(m.get("width", 0) * m.get("height", 0) 
                               for m in metadata) / max(len(metadata), 1),
            "total_files": len(metadata)
        }
    
    def save_dataset(self, output_path: str):
        """Save dataset to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.dataset, f, indent=2)
        print(f"Dataset saved to: {output_path}")
        
    def load_dataset(self, input_path: str) -> Dict[str, Any]:
        """Load dataset from JSON file."""
        with open(input_path, 'r') as f:
            self.dataset = json.load(f)
        return self.dataset
    
    def filter_by_style(self, style: str) -> List[Dict[str, Any]]:
        """Filter regions by architectural style."""
        return [r for r in self.dataset.get("regions", []) 
                if r.get("style") == style]
    
    def filter_by_type(self, region_type: str) -> List[Dict[str, Any]]:
        """Filter regions by type."""
        return [r for r in self.dataset.get("regions", []) 
                if r.get("region_type") == region_type]
    
    def get_style_examples(self, style: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get example regions for a specific style."""
        regions = self.filter_by_style(style)
        return regions[:count]
    
    def get_type_examples(self, region_type: str, 
                         count: int = 10) -> List[Dict[str, Any]]:
        """Get example regions for a specific type."""
        regions = self.filter_by_type(region_type)
        return regions[:count]