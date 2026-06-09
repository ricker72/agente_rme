"""
HITO 17 — Pattern Miner: Mines recurring architectural patterns from blueprints and analyses.

Extracts reusable patterns for:
- Temples: altar layouts, pillar arrangements, sacred geometry
- Depots: locker placement, access patterns, security features
- Markets: stall arrangements, NPC positioning, trade routes
- Boss Rooms: arena layouts, spawn points, mechanics zones
- Houses: room configurations, furniture patterns, entrance styles
- Bridges: span types, support structures, crossing patterns
- Camps: fire pits, tent arrangements, perimeter defenses
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from core.analyzer.map_analyzer import MapAnalysis
from core.blueprints.blueprint import Blueprint


@dataclass
class MinedPattern:
    """A mined architectural pattern."""
    pattern_id: str
    pattern_type: str  # temple, depot, market, boss_room, house, bridge, camp
    name: str
    description: str
    
    # Structural features
    layout_signature: Dict[str, float]  # grid, linear, radial, organic scores
    room_template: Dict[str, Any]  # typical room sizes, shapes, connections
    feature_distribution: Dict[str, float]  # item/ground frequencies
    
    # Spatial metrics
    typical_size: Tuple[int, int]  # (width, height)
    aspect_ratio: float
    density: float
    symmetry_score: float
    
    # Key elements
    required_grounds: List[int]
    required_items: List[int]
    optional_items: List[int]
    spawn_patterns: List[Dict[str, Any]]
    
    # Quality metrics
    sample_count: int
    confidence: float
    variability: float  # how consistent across samples
    
    # Generation hints
    generation_hints: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MinedPattern:
        return cls(**data)


class PatternMiner:
    """
    Mines recurring patterns from map analyses and blueprints.
    
    Uses:
    - Spatial clustering of similar structures
    - Statistical aggregation of ground/item distributions
    - Layout signature extraction
    - Variability analysis for generation guidance
    """
    
    # Structure type detection keywords
    STRUCTURE_KEYWORDS = {
        "temple": ["temple", "altar", "shrine", "sanctuary", "chapel", "church", "polished_stone", "temple_npc"],
        "depot": ["depot", "locker", "depot_npc", "storage", "warehouse"],
        "market": ["market", "shop", "stall", "merchant", "trader", "vendor", "price"],
        "boss_room": ["boss", "throne", "boss_room", "arena_boss", "demon", "dragon_lord", "ferumbras"],
        "house": ["house", "residential", "bedroom", "living", "kitchen", "citizen"],
        "bridge": ["bridge", "crossing", "span", "river_cross", "bridge_section"],
        "camp": ["camp", "tent", "campfire", "camp_tent", "bandit_camp", "outpost", "watchtower"],
        "dungeon_entrance": ["entrance", "portal", "dungeon_enter", "stairs_down", "hole", "ladder_down"],
        "arena": ["arena", "coliseum", "arena_floor", "spectator", "combat_pit"],
        "library": ["library", "bookcase", "scroll", "knowledge", "archive", "librarian"],
        "prison": ["prison", "cell", "cage", "prisoner", "jail", "bars", "dungeon_cell"],
        "throne_room": ["throne", "throne_room", "king", "queen", "ruler", "monarch"],
        "crypt": ["crypt", "tomb", "grave", "coffin", "sarcophagus", "undead", "necromancer"],
        "altar": ["altar", "sacrificial", "ritual", "ceremony", "prayer"],
        "shrine": ["shrine", "offering", "blessing", "devotion", "holy_site"],
        "guildhall": ["guild", "guildhall", "guild_hall", "faction", "order"],
        "tavern": ["tavern", "inn", "bar", "pub", "drink", "bartender", "alcohol"],
        "shop": ["shop", "store", "buy", "sell", "merchant", "trader"],
        "workshop": ["workshop", "forge", "anvil", "crafting", "blacksmith", "carpenter"],
        "farm": ["farm", "field", "crop", "farmer", "barn", "stable", "animal"],
        "mine": ["mine", "ore", "mining", "pickaxe", "vein", "miner", "tunnel"],
        "cave": ["cave", "cavern", "grotto", "stalactite", "underground"],
        "ruins": ["ruin", "ruins", "ancient", "collapsed", "rubble", "decayed"],
        "tower": ["tower", "spire", "watchtower", "tower_top", "observatory"],
        "wall_section": ["wall", "fortification", "rampart", "battlement", "palisade"],
        "gate": ["gate", "gatehouse", "portcullis", "drawbridge", "entrance_gate"],
    }
    
    def __init__(self, min_samples: int = 3):
        """
        Initialize the pattern miner.
        
        Args:
            min_samples: Minimum samples needed to form a pattern
        """
        self.min_samples = min_samples
        self.mined_patterns: Dict[str, MinedPattern] = {}
        self.raw_samples: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._trained = False
    
    def mine_from_analysis(self, analysis: MapAnalysis) -> List[MinedPattern]:
        """
        Mine patterns from a single map analysis.
        
        Args:
            analysis: MapAnalysis from MapAnalyzer
            
        Returns:
            List of mined patterns
        """
        patterns = []
        
        # Create sample data from analysis
        sample = self._analysis_to_sample(analysis)
        
        # Detect structure types present
        structure_types = self._detect_structure_types(analysis)
        
        for struct_type in structure_types:
            if struct_type not in self.raw_samples:
                self.raw_samples[struct_type] = []
            self.raw_samples[struct_type].append(sample)
            
            # If we have enough samples, mine pattern
            if len(self.raw_samples[struct_type]) >= self.min_samples:
                pattern = self._mine_pattern_for_type(struct_type)
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    def learn_from_blueprints(self, blueprints: List[Blueprint]):
        """
        Learn patterns from a collection of blueprints.
        
        Args:
            blueprints: List of Blueprint objects
        """
        for bp in blueprints:
            # Convert blueprint to sample format
            sample = self._blueprint_to_sample(bp)
            
            # Detect structure type from blueprint
            struct_type = self._blueprint_to_structure_type(bp)
            
            if struct_type not in self.raw_samples:
                self.raw_samples[struct_type] = []
            self.raw_samples[struct_type].append(sample)
        
        # Mine patterns for all types with enough samples
        for struct_type, samples in self.raw_samples.items():
            if len(samples) >= self.min_samples:
                pattern = self._mine_pattern_for_type(struct_type)
                if pattern:
                    self.mined_patterns[struct_type] = pattern
        
        self._trained = True
    
    def _analysis_to_sample(self, analysis: MapAnalysis) -> Dict[str, Any]:
        """Convert MapAnalysis to sample format."""
        return {
            "source": analysis.source,
            "map_size": analysis.map_size,
            "tiles": analysis.tiles,
            "items": analysis.items,
            "spawns": analysis.spawns,
            "houses": analysis.houses,
            "waypoints": analysis.waypoints,
            "zones": analysis.zones,
            "style": analysis.style,
            "floors": analysis.floors,
            "tile_count": analysis.tile_count,
            "item_count": analysis.item_count,
        }
    
    def _blueprint_to_sample(self, bp: Blueprint) -> Dict[str, Any]:
        """Convert Blueprint to sample format."""
        # Aggregate tile stats from blueprint
        grounds = {}
        items = {}
        for tile in bp.tiles:
            g = f"ground_{tile.ground}"
            grounds[g] = grounds.get(g, 0) + 1
            if tile.item:
                i = f"item_{tile.item}"
                items[i] = items.get(i, 0) + 1
        
        spawns = []
        for tile in bp.tiles:
            if tile.spawn:
                spawns.append(tile.spawn)
        
        return {
            "source": bp.name,
            "map_size": {"width": bp.width, "height": bp.height},
            "tiles": grounds,
            "items": items,
            "spawns": spawns,
            "houses": [],
            "waypoints": [],
            "zones": bp.zones,
            "style": bp.theme,
            "floors": [0],
            "tile_count": len(bp.tiles),
            "item_count": sum(items.values()),
            "rooms": bp.rooms,
            "features": bp.features,
            "category": bp.category,
            "metadata": {
                "difficulty": bp.metadata.difficulty,
                "tags": bp.metadata.tags,
            }
        }
    
    def _detect_structure_types(self, analysis: MapAnalysis) -> List[str]:
        """Detect which structure types are present in the analysis."""
        detected = []
        
        # Combine all text data for keyword matching
        all_text = " ".join([
            str(analysis.tiles).lower(),
            str(analysis.items).lower(),
            " ".join(str(s.get("monster", "")).lower() for s in analysis.spawns),
            " ".join(str(h.get("name", "")).lower() for h in analysis.houses),
            " ".join(str(w.get("name", "")).lower() for w in analysis.waypoints),
            str(analysis.style).lower(),
        ])
        
        for struct_type, keywords in self.STRUCTURE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in all_text:
                    detected.append(struct_type)
                    break
        
        return list(set(detected))
    
    def _blueprint_to_structure_type(self, bp: Blueprint) -> str:
        """Determine structure type from blueprint."""
        # Use category primarily
        if bp.category in self.STRUCTURE_KEYWORDS:
            return bp.category
        
        # Fall back to theme
        if bp.theme in self.STRUCTURE_KEYWORDS:
            return bp.theme
        
        # Check tags
        for tag in bp.metadata.tags:
            if tag in self.STRUCTURE_KEYWORDS:
                return tag
        
        return "unknown"
    
    def _mine_pattern_for_type(self, struct_type: str) -> Optional[MinedPattern]:
        """Mine a pattern for a specific structure type."""
        samples = self.raw_samples[struct_type]
        if len(samples) < self.min_samples:
            return None
        
        pattern_id = f"pattern_{struct_type}_{len(samples)}"
        
        # Aggregate ground distributions
        all_grounds = Counter()
        all_items = Counter()
        all_spawn_monsters = Counter()
        all_room_sizes = []
        all_dimensions = []
        
        for sample in samples:
            # Grounds
            for ground, count in sample.get("tiles", {}).items():
                all_grounds[ground] += count
            
            # Items
            for item, count in sample.get("items", {}).items():
                all_items[item] += count
            
            # Spawns
            for spawn in sample.get("spawns", []):
                monster = spawn.get("monster", "") if isinstance(spawn, dict) else str(spawn)
                if monster:
                    all_spawn_monsters[monster] += 1
            
            # Dimensions
            map_size = sample.get("map_size", {})
            w = map_size.get("width", 0)
            h = map_size.get("height", 0)
            if w > 0 and h > 0:
                all_dimensions.append((w, h))
            
            # Room sizes
            for room in sample.get("rooms", []):
                bounds = room.get("bounds", [0, 0, 0, 0])
                rw = bounds[2] - bounds[0]
                rh = bounds[3] - bounds[1]
                if rw > 0 and rh > 0:
                    all_room_sizes.append((rw, rh))
        
        # Compute layout signature
        layout_sig = self._compute_layout_signature(samples)
        
        # Typical size
        if all_dimensions:
            avg_w = np.mean([d[0] for d in all_dimensions])
            avg_h = np.mean([d[1] for d in all_dimensions])
            typical_size = (int(avg_w), int(avg_h))
            aspect_ratio = avg_w / max(avg_h, 1)
        else:
            typical_size = (50, 50)
            aspect_ratio = 1.0
        
        # Density
        total_tiles = sum(all_grounds.values())
        total_area = max(typical_size[0] * typical_size[1], 1)
        density = total_tiles / total_area
        
        # Symmetry (from layout signature)
        symmetry_score = layout_sig.get("symmetry", 0.5)
        
        # Required/optional items
        total_samples = len(samples)
        required_items = []
        optional_items = []
        
        for item, count in all_items.items():
            freq = count / total_samples
            if freq >= 0.7:
                required_items.append(int(item.replace("item_", "")))
            elif freq >= 0.3:
                optional_items.append(int(item.replace("item_", "")))
        
        required_grounds = []
        for ground, count in all_grounds.items():
            freq = count / total_samples
            if freq >= 0.5:
                required_grounds.append(int(ground.replace("ground_", "")))
        
        # Spawn patterns
        spawn_patterns = []
        for monster, count in all_spawn_monsters.items():
            if count >= total_samples * 0.3:
                spawn_patterns.append({
                    "monster": monster,
                    "frequency": count / total_samples,
                    "count_per_map": count / total_samples,
                })
        
        # Room template
        room_template = {}
        if all_room_sizes:
            avg_rw = np.mean([s[0] for s in all_room_sizes])
            avg_rh = np.mean([s[1] for s in all_room_sizes])
            # Count rooms per sample
            rooms_per_sample = []
            for sample in samples:
                room_count = len(sample.get("rooms", []))
                if room_count == 0:
                    # Estimate from bounds
                    room_count = 1
                rooms_per_sample.append(room_count)
            room_template = {
                "typical_width": int(avg_rw),
                "typical_height": int(avg_rh),
                "aspect_ratio": avg_rw / max(avg_rh, 1),
                "count_range": [min(rooms_per_sample) if rooms_per_sample else 1, 
                               max(rooms_per_sample) if rooms_per_sample else 1],
            }
        
        # Feature distribution (normalized)
        feature_dist = {}
        total_features = sum(all_items.values()) + sum(all_grounds.values())
        if total_features > 0:
            for item, count in all_items.most_common(20):
                feature_dist[item] = count / total_features
            for ground, count in all_grounds.most_common(20):
                feature_dist[ground] = count / total_features
        
        # Variability (how consistent across samples)
        variability = self._compute_variability(samples)
        
        # Generation hints
        gen_hints = self._generate_hints(struct_type, layout_sig, required_grounds, required_items, spawn_patterns)
        
        return MinedPattern(
            pattern_id=pattern_id,
            pattern_type=struct_type,
            name=f"{struct_type.replace('_', ' ').title()} Pattern",
            description=f"Mined from {len(samples)} {struct_type} samples",
            layout_signature=layout_sig,
            room_template=room_template,
            feature_distribution=feature_dist,
            typical_size=typical_size,
            aspect_ratio=aspect_ratio,
            density=density,
            symmetry_score=symmetry_score,
            required_grounds=required_grounds,
            required_items=required_items,
            optional_items=optional_items,
            spawn_patterns=spawn_patterns,
            sample_count=len(samples),
            confidence=min(1.0, len(samples) / 10.0),
            variability=variability,
            generation_hints=gen_hints,
        )
    
    def _compute_layout_signature(self, samples: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute layout signature from samples."""
        # Aggregate layout features
        grid_scores = []
        linear_scores = []
        radial_scores = []
        organic_scores = []
        symmetry_scores = []
        
        for sample in samples:
            # Try to extract from zones/architecture analysis
            zones = sample.get("zones", [])
            if zones:
                for zone in zones:
                    props = zone.get("properties", {})
                    layout = props.get("layout_type", "")
                    if layout == "grid":
                        grid_scores.append(1.0)
                        linear_scores.append(0.0)
                        radial_scores.append(0.0)
                        organic_scores.append(0.0)
                    elif layout == "linear":
                        grid_scores.append(0.0)
                        linear_scores.append(1.0)
                        radial_scores.append(0.0)
                        organic_scores.append(0.0)
                    elif layout == "radial":
                        grid_scores.append(0.0)
                        linear_scores.append(0.0)
                        radial_scores.append(1.0)
                        organic_scores.append(0.0)
                    else:
                        grid_scores.append(0.2)
                        linear_scores.append(0.2)
                        radial_scores.append(0.2)
                        organic_scores.append(1.0)
        
        return {
            "grid": np.mean(grid_scores) if grid_scores else 0.25,
            "linear": np.mean(linear_scores) if linear_scores else 0.25,
            "radial": np.mean(radial_scores) if radial_scores else 0.25,
            "organic": np.mean(organic_scores) if organic_scores else 0.25,
            "symmetry": np.mean(symmetry_scores) if symmetry_scores else 0.5,
        }
    
    def _compute_variability(self, samples: List[Dict[str, Any]]) -> float:
        """Compute how variable the samples are."""
        if len(samples) < 2:
            return 0.0
        
        # Compare ground distributions
        ground_vectors = []
        for sample in samples:
            grounds = sample.get("tiles", {})
            # Normalize
            total = sum(grounds.values())
            if total > 0:
                vec = {k: v / total for k, v in grounds.items()}
                ground_vectors.append(vec)
        
        if len(ground_vectors) < 2:
            return 0.0
        
        # Average pairwise distance
        distances = []
        keys = set().union(*ground_vectors)
        for i in range(len(ground_vectors)):
            for j in range(i + 1, len(ground_vectors)):
                diff = 0
                for k in keys:
                    diff += abs(ground_vectors[i].get(k, 0) - ground_vectors[j].get(k, 0))
                distances.append(diff)
        
        return np.mean(distances) if distances else 0.0
    
    def _generate_hints(
        self,
        struct_type: str,
        layout_sig: Dict[str, float],
        required_grounds: List[int],
        required_items: List[int],
        spawn_patterns: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate generation hints for this pattern type."""
        hints = {
            "layout_preference": max(layout_sig, key=layout_sig.get) if layout_sig else "organic",
            "required_grounds": required_grounds[:5],
            "required_items": required_items[:10],
            "optional_items": [],
            "size_range": {"min": 20, "max": 100},
            "room_count_range": {"min": 1, "max": 10},
            "spawn_patterns": spawn_patterns,
        }
        
        # Type-specific hints
        type_hints = {
            "temple": {
                "central_altar": True,
                "pillar_grid": True,
                "sacred_geometry": "radial",
                "entrance_formal": True,
            },
            "depot": {
                "locker_wall": True,
                "npc_near_entrance": True,
                "open_floor": True,
                "security_items": [5000, 5001],
            },
            "market": {
                "stall_rows": True,
                "central_plaza": True,
                "npc_vendors": True,
                "item_display": True,
            },
            "boss_room": {
                "arena_layout": True,
                "boss_platform": True,
                "mechanics_zones": True,
                "escape_routes": False,
            },
            "house": {
                "room_cluster": True,
                "entrance_area": True,
                "furniture_patterns": True,
                "residential_items": True,
            },
            "bridge": {
                "linear_span": True,
                "support_pillars": True,
                "railing": True,
                "crossing_type": "river",
            },
            "camp": {
                "perimeter": True,
                "central_fire": True,
                "tent_circle": True,
                "watch_positions": True,
            },
        }
        
        if struct_type in type_hints:
            hints.update(type_hints[struct_type])
        
        return hints
    
    def get_pattern(self, pattern_type: str) -> Optional[MinedPattern]:
        """Get a mined pattern by type."""
        return self.mined_patterns.get(pattern_type)
    
    def list_patterns(self) -> List[str]:
        """List all mined pattern types."""
        return list(self.mined_patterns.keys())
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about mined patterns."""
        stats = {}
        for ptype, pattern in self.mined_patterns.items():
            stats[ptype] = {
                "sample_count": pattern.sample_count,
                "confidence": pattern.confidence,
                "variability": pattern.variability,
                "typical_size": pattern.typical_size,
                "layout": pattern.layout_signature,
            }
        return stats
    
    def generate_pattern_guide(self, pattern_type: str = None) -> Dict[str, Any]:
        """Generate a pattern guide for map generation."""
        if pattern_type:
            pattern = self.mined_patterns.get(pattern_type)
            if not pattern:
                return {}
            return pattern.generation_hints
        
        # Return all guides
        guides = {}
        for ptype, pattern in self.mined_patterns.items():
            guides[ptype] = pattern.generation_hints
        return guides
    
    def save_patterns(self, output_path: str):
        """Save mined patterns to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "min_samples": self.min_samples,
            "patterns": {},
            "raw_sample_counts": {k: len(v) for k, v in self.raw_samples.items()},
        }
        
        for ptype, pattern in self.mined_patterns.items():
            data["patterns"][ptype] = pattern.to_dict()
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_patterns(self, input_path: str):
        """Load mined patterns from file."""
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        self.min_samples = data.get("min_samples", self.min_samples)
        self.mined_patterns = {}
        
        for ptype, pattern_data in data.get("patterns", {}).items():
            self.mined_patterns[ptype] = MinedPattern.from_dict(pattern_data)
        
        # Raw samples would need to be rebuilt from blueprints
        self._trained = True