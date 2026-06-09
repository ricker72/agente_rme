"""
Style Encoder - Learns and encodes architectural styles from OpenTibia maps.

This module focuses on learning the distinctive architectural characteristics
of different OpenTibia areas such as Issavi, Roshamuul, Soul War, Library,
Falcon, and Cobra areas.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
import json
import os
from collections import Counter, defaultdict


@dataclass
class StyleProfile:
    """Represents the learned profile of an architectural style."""
    style_name: str
    sample_count: int
    
    # Ground tile preferences
    ground_preferences: Dict[str, float]
    
    # Wall tile preferences
    wall_preferences: Dict[str, float]
    
    # Item preferences
    item_preferences: Dict[str, float]
    
    # Structural patterns
    avg_room_size: float
    avg_corridor_length: float
    room_shape_distribution: Dict[str, float]
    connectivity_ratio: float
    
    # Atmospheric features
    lighting_preference: str  # bright, dim, dark
    decoration_density: float
    common_effects: List[str]
    
    # Color palette (if applicable)
    dominant_colors: List[Tuple[int, int, int]]
    
    # Embedding centroid
    centroid_vector: List[float]
    
    # Variance in style
    style_variance: float


class StyleEncoder:
    """
    Encodes and learns architectural styles from map data.
    
    The encoder analyzes map regions to identify and characterize
    distinct architectural styles, building profiles that capture
    the essence of each style.
    """
    
    # Known OpenTibia architectural styles
    KNOWN_STYLES = {
        "issavi": {
            "description": "Ancient desert city with sandy tones and ruins",
            "typical_grounds": ["sand", "ancient_stone", "desert_tile", 
                               "sandstone", "ruins_tile"],
            "typical_walls": ["sandstone_wall", "ancient_wall", "desert_brick"],
            "lighting": "bright",
            "color_palette": [(210, 180, 140), (180, 150, 110), (200, 170, 130)]
        },
        "roshamuul": {
            "description": "Dark prison island with grim architecture",
            "typical_grounds": ["roshamuul_stone", "prison_floor", "dark_tile",
                               "grim_stone", "cell_floor"],
            "typical_walls": ["prison_wall", "iron_bars", "dark_brick",
                             "stone_bars"],
            "lighting": "dark",
            "color_palette": [(80, 80, 80), (60, 60, 60), (100, 100, 100)]
        },
        "soulwar": {
            "description": "Spiritual warfare zone with ethereal elements",
            "typical_grounds": ["soul_stone", "war_stone", "spirit_tile",
                               "ethereal_floor", "battle_ground"],
            "typical_walls": ["soul_wall", "war_brick", "spirit_barrier"],
            "lighting": "dim",
            "color_palette": [(150, 120, 180), (180, 150, 200), (120, 100, 160)]
        },
        "library": {
            "description": "Scholarly area with bookshelves and study spaces",
            "typical_grounds": ["library_floor", "wooden_floor", "carpet",
                               "study_tile"],
            "typical_walls": ["bookshelf", "wooden_wall", "stone_brick"],
            "lighting": "dim",
            "color_palette": [(139, 90, 43), (101, 67, 33), (160, 120, 60)]
        },
        "falcon": {
            "description": "Noble area with bird motifs and elegant design",
            "typical_grounds": ["falcon_tile", "marble_floor", "eagle_symbol",
                               "noble_stone"],
            "typical_walls": ["falcon_wall", "marble_brick", "ornate_wall"],
            "lighting": "bright",
            "color_palette": [(200, 180, 150), (180, 160, 130), (220, 200, 170)]
        },
        "cobra": {
            "description": "Serpent-themed area with exotic designs",
            "typical_grounds": ["cobra_tile", "serpent_stone", "snake_symbol",
                               "exotic_floor"],
            "typical_walls": ["cobra_wall", "serpent_brick", "exotic_wall"],
            "lighting": "dim",
            "color_palette": [(80, 120, 80), (60, 100, 60), (100, 140, 100)]
        },
        "yalahar": {
            "description": "Mysterious city with unique architecture",
            "typical_grounds": ["yalahar_stone", "mystery_tile", "ancient_paver"],
            "typical_walls": ["yalahar_wall", "mystery_brick"],
            "lighting": "dim",
            "color_palette": [(100, 100, 120), (80, 80, 100), (120, 120, 140)]
        },
        "thais": {
            "description": "Classic human city with traditional design",
            "typical_grounds": ["stone_floor", "wooden_floor", "tile"],
            "typical_walls": ["stone_brick", "wooden_wall"],
            "lighting": "bright",
            "color_palette": [(160, 140, 120), (140, 120, 100), (180, 160, 140)]
        }
    }
    
    def __init__(self, styles: List[str] = None):
        """
        Initialize the style encoder.
        
        Args:
            styles: Optional list of styles to focus on
        """
        self.styles = styles or list(self.KNOWN_STYLES.keys())
        self.style_profiles: Dict[str, StyleProfile] = {}
        self.style_samples: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._trained = False
        
    def add_sample(self, style: str, region_data: Dict[str, Any]):
        """
        Add a sample region to a style's training data.
        
        Args:
            style: Style name
            region_data: Region data dictionary
        """
        if style not in self.styles:
            self.styles.append(style)
        self.style_samples[style].append(region_data)
        self._trained = False
        
    def _extract_ground_distribution(self, region_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract ground tile distribution from region."""
        ground_counts = Counter()
        tiles = region_data.get("tiles", [])
        
        for tile in tiles:
            ground = tile.get("ground", "unknown")
            ground_counts[ground] += 1
            
        return dict(ground_counts)
    
    def _extract_wall_distribution(self, region_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract wall tile distribution from region."""
        wall_counts = Counter()
        tiles = region_data.get("tiles", [])
        
        for tile in tiles:
            items = tile.get("items", [])
            for item in items:
                if "wall" in item.get("type", "").lower() or \
                   "wall" in item.get("name", "").lower():
                    wall_counts[item.get("name", item.get("type"))] += 1
                    
        return dict(wall_counts)
    
    def _extract_item_distribution(self, region_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract item distribution from region."""
        item_counts = Counter()
        tiles = region_data.get("tiles", [])
        
        for tile in tiles:
            items = tile.get("items", [])
            for item in items:
                item_name = item.get("name", item.get("type", "unknown"))
                item_counts[item_name] += 1
                
        return dict(item_counts)
    
    def _extract_room_statistics(self, region_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract room statistics from region."""
        rooms = region_data.get("rooms", [])
        
        if not rooms:
            return {
                "avg_room_size": 0,
                "room_shape_distribution": {},
                "connectivity_ratio": 0
            }
            
        sizes = [r.get("area", 0) for r in rooms]
        shapes = [r.get("shape", "unknown") for r in rooms]
        connections = region_data.get("connections", [])
        
        shape_dist = dict(Counter(shapes))
        total = len(shapes)
        shape_dist = {k: v/total for k, v in shape_dist.items()}
        
        conn_ratio = len(connections) / max(len(rooms), 1)
        
        return {
            "avg_room_size": np.mean(sizes) if sizes else 0,
            "room_shape_distribution": shape_dist,
            "connectivity_ratio": conn_ratio
        }
    
    def _extract_corridor_statistics(self, region_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract corridor statistics from region."""
        corridors = region_data.get("corridors", [])
        
        if not corridors:
            return {"avg_corridor_length": 0}
            
        lengths = [c.get("length", 0) for c in corridors]
        return {"avg_corridor_length": np.mean(lengths)}
    
    def _extract_decoration_density(self, region_data: Dict[str, Any]) -> float:
        """Calculate decoration density of a region."""
        tiles = region_data.get("tiles", [])
        decorations = 0
        
        decorative_types = {"decoration", "ornament", "statue", "painting",
                          "carpet", "plant", "furniture", "lamp", "candle"}
        
        for tile in tiles:
            items = tile.get("items", [])
            for item in items:
                item_type = item.get("type", "").lower()
                if any(dt in item_type for dt in decorative_types):
                    decorations += 1
                    
        return decorations / max(len(tiles), 1)
    
    def _determine_lighting(self, region_data: Dict[str, Any]) -> str:
        """Determine the lighting preference of a region."""
        # Check for light sources
        tiles = region_data.get("tiles", [])
        light_sources = 0
        dark_tiles = 0
        
        light_types = {"lamp", "torch", "candle", "lantern", "light"}
        dark_types = {"dark", "shadow", "dim"}
        
        for tile in tiles:
            items = tile.get("items", [])
            ground = tile.get("ground", "").lower()
            
            for item in items:
                item_type = item.get("type", "").lower()
                if any(lt in item_type for lt in light_types):
                    light_sources += 1
                    
            if any(dt in ground for dt in dark_types):
                dark_tiles += 1
                
        total = max(len(tiles), 1)
        light_ratio = light_sources / total
        dark_ratio = dark_tiles / total
        
        if dark_ratio > 0.3:
            return "dark"
        elif light_ratio > 0.1:
            return "bright"
        else:
            return "dim"
    
    def train(self, dataset: Dict[str, Any] = None):
        """
        Train the style encoder on a dataset.
        
        Args:
            dataset: Dataset dictionary from DatasetBuilder
        """
        if dataset:
            regions = dataset.get("regions", [])
            for region in regions:
                style = region.get("style")
                if style and style in self.styles:
                    self.add_sample(style, region)
                    
        # Build style profiles
        for style in self.styles:
            samples = self.style_samples.get(style, [])
            if not samples:
                continue
                
            self.style_profiles[style] = self._build_style_profile(style, samples)
            
        self._trained = True
        
    def _build_style_profile(self, style: str, 
                            samples: List[Dict[str, Any]]) -> StyleProfile:
        """Build a style profile from samples."""
        # Aggregate ground preferences
        ground_counter = Counter()
        wall_counter = Counter()
        item_counter = Counter()
        
        room_sizes = []
        corridor_lengths = []
        shape_counters = Counter()
        connectivity_ratios = []
        decoration_densities = []
        lighting_votes = []
        
        for sample in samples:
            # Ground and wall distributions
            grounds = self._extract_ground_distribution(sample)
            walls = self._extract_wall_distribution(sample)
            items = self._extract_item_distribution(sample)
            
            for k, v in grounds.items():
                ground_counter[k] += v
            for k, v in walls.items():
                wall_counter[k] += v
            for k, v in items.items():
                item_counter[k] += v
                
            # Room statistics
            room_stats = self._extract_room_statistics(sample)
            room_sizes.append(room_stats["avg_room_size"])
            for shape, count in room_stats["room_shape_distribution"].items():
                shape_counters[shape] += count
            connectivity_ratios.append(room_stats["connectivity_ratio"])
            
            # Corridor statistics
            corridor_stats = self._extract_corridor_statistics(sample)
            corridor_lengths.append(corridor_stats["avg_corridor_length"])
            
            # Decoration density
            decoration_densities.append(self._extract_decoration_density(sample))
            
            # Lighting
            lighting_votes.append(self._determine_lighting(sample))
            
        # Normalize distributions
        total_grounds = sum(ground_counter.values()) or 1
        total_walls = sum(wall_counter.values()) or 1
        total_items = sum(item_counter.values()) or 1
        
        ground_prefs = {k: v/total_grounds for k, v in ground_counter.most_common(20)}
        wall_prefs = {k: v/total_walls for k, v in wall_counter.most_common(20)}
        item_prefs = {k: v/total_items for k, v in item_counter.most_common(30)}
        
        # Shape distribution
        total_shapes = sum(shape_counters.values()) or 1
        shape_dist = {k: v/total_shapes for k, v in shape_counters.most_common()}
        
        # Dominant lighting
        lighting = Counter(lighting_votes).most_common(1)[0][0] if lighting_votes else "dim"
        
        # Get style info from known styles
        style_info = self.KNOWN_STYLES.get(style, {})
        color_palette = style_info.get("color_palette", [(128, 128, 128)])
        
        # Create centroid vector (simplified - would use actual embeddings in production)
        centroid = np.random.randn(128).tolist()  # Placeholder
        
        # Calculate style variance
        style_variance = np.std(room_sizes) if room_sizes else 0
        
        return StyleProfile(
            style_name=style,
            sample_count=len(samples),
            ground_preferences=ground_prefs,
            wall_preferences=wall_prefs,
            item_preferences=item_prefs,
            avg_room_size=np.mean(room_sizes) if room_sizes else 0,
            avg_corridor_length=np.mean(corridor_lengths) if corridor_lengths else 0,
            room_shape_distribution=shape_dist,
            connectivity_ratio=np.mean(connectivity_ratios) if connectivity_ratios else 0,
            lighting_preference=lighting,
            decoration_density=np.mean(decoration_densities) if decoration_densities else 0,
            common_effects=[],
            dominant_colors=color_palette,
            centroid_vector=centroid,
            style_variance=style_variance
        )
    
    def encode_style(self, style: str, region_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Encode a region's adherence to a specific style.
        
        Args:
            style: Style name to check against
            region_data: Region data to encode
            
        Returns:
            Dictionary of style adherence scores
        """
        profile = self.style_profiles.get(style)
        if not profile:
            return {"adherence": 0.0}
            
        # Extract features from region
        grounds = self._extract_ground_distribution(region_data)
        walls = self._extract_wall_distribution(region_data)
        
        # Calculate ground match
        ground_score = 0
        total_grounds = sum(grounds.values()) or 1
        for ground, pref in profile.ground_preferences.items():
            actual = grounds.get(ground, 0) / total_grounds
            ground_score += min(actual, pref)
            
        # Calculate wall match
        wall_score = 0
        total_walls = sum(walls.values()) or 1
        for wall, pref in profile.wall_preferences.items():
            actual = walls.get(wall, 0) / total_walls
            wall_score += min(actual, pref)
            
        # Calculate overall adherence
        adherence = (ground_score * 0.6 + wall_score * 0.4)
        
        return {
            "adherence": adherence,
            "ground_match": ground_score,
            "wall_match": wall_score
        }
    
    def classify_style(self, region_data: Dict[str, Any]) -> Tuple[str, float]:
        """
        Classify a region's architectural style.
        
        Args:
            region_data: Region data to classify
            
        Returns:
            Tuple of (style_name, confidence)
        """
        scores = {}
        
        for style in self.styles:
            profile = self.style_profiles.get(style)
            if not profile:
                continue
                
            encoding = self.encode_style(style, region_data)
            scores[style] = encoding["adherence"]
            
        if not scores:
            return ("unknown", 0.0)
            
        best_style = max(scores, key=scores.get)
        confidence = scores[best_style]
        
        return (best_style, confidence)
    
    def get_style_profile(self, style: str) -> Optional[StyleProfile]:
        """Get the profile for a specific style."""
        return self.style_profiles.get(style)
    
    def list_styles(self) -> List[str]:
        """List all known styles."""
        return self.styles
    
    def get_style_statistics(self) -> Dict[str, Any]:
        """Get statistics about learned styles."""
        stats = {}
        for style, profile in self.style_profiles.items():
            stats[style] = {
                "sample_count": profile.sample_count,
                "avg_room_size": profile.avg_room_size,
                "avg_corridor_length": profile.avg_corridor_length,
                "connectivity_ratio": profile.connectivity_ratio,
                "decoration_density": profile.decoration_density,
                "lighting": profile.lighting_preference,
                "top_grounds": list(profile.ground_preferences.keys())[:5],
                "top_walls": list(profile.wall_preferences.keys())[:5]
            }
        return stats
    
    def save_profiles(self, output_path: str):
        """Save style profiles to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = {
            "version": "1.0",
            "styles": self.styles,
            "profiles": {}
        }
        
        for style, profile in self.style_profiles.items():
            data["profiles"][style] = asdict(profile)
            
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_profiles(self, input_path: str):
        """Load style profiles from file."""
        with open(input_path, 'r') as f:
            data = json.load(f)
            
        self.styles = data.get("styles", [])
        self.style_profiles = {}
        
        for style, profile_data in data.get("profiles", {}).items():
            self.style_profiles[style] = StyleProfile(**profile_data)
            
        self._trained = True
        
    def generate_style_guide(self, style: str) -> Dict[str, Any]:
        """
        Generate a style guide for map generation.
        
        Args:
            style: Style name
            
        Returns:
            Style guide dictionary for use in map generation
        """
        profile = self.style_profiles.get(style)
        if not profile:
            # Return default guide from known styles
            style_info = self.KNOWN_STYLES.get(style, {})
            return {
                "style": style,
                "description": style_info.get("description", f"Generated {style} style"),
                "recommended_grounds": style_info.get("typical_grounds", []),
                "recommended_walls": style_info.get("typical_walls", []),
                "lighting": style_info.get("lighting", "dim"),
                "color_palette": style_info.get("color_palette", []),
                "avg_room_size": 100,
                "avg_corridor_length": 20,
                "decoration_density": 0.1
            }
            
        return {
            "style": style,
            "description": self.KNOWN_STYLES.get(style, {}).get("description", ""),
            "recommended_grounds": list(profile.ground_preferences.keys())[:10],
            "recommended_walls": list(profile.wall_preferences.keys())[:10],
            "lighting": profile.lighting_preference,
            "color_palette": profile.dominant_colors,
            "avg_room_size": profile.avg_room_size,
            "avg_corridor_length": profile.avg_corridor_length,
            "connectivity_ratio": profile.connectivity_ratio,
            "decoration_density": profile.decoration_density,
            "room_shape_preferences": profile.room_shape_distribution
        }