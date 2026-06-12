"""
Map Embedding - Creates vector representations for OpenTibia map regions.

This module generates numerical embeddings for different map types including
cities, dungeons, boss rooms, and temples, enabling similarity comparisons
and pattern learning.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import hashlib
import os


@dataclass
class MapEmbedding:
    """Represents a vector embedding of a map region."""

    embedding_id: str
    region_id: str
    region_type: str
    style: Optional[str]
    vector: List[float]
    dimensions: int
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MapEmbedding":
        """Create from dictionary."""
        return cls(**data)


class MapEmbedder:
    """
    Generates vector embeddings for map regions.

    The embedder creates numerical representations that capture the
    essential characteristics of map regions, enabling similarity
    comparisons and machine learning operations.
    """

    # Default embedding dimensions
    DEFAULT_DIMENSIONS = 128

    # Embedding dimensions for different region types
    TYPE_DIMENSIONS = {
        "city": 256,
        "dungeon": 192,
        "boss_room": 128,
        "temple": 128,
        "cave": 160,
        "tower": 128,
        "default": 128,
    }

    def __init__(self, dimensions: int = None, model_path: str = None):
        """
        Initialize the map embedder.

        Args:
            dimensions: Embedding vector dimensions
            model_path: Path to pre-trained model weights
        """
        self.dimensions = dimensions or self.DEFAULT_DIMENSIONS
        self.model_path = model_path
        self._model_weights: Optional[Dict[str, np.ndarray]] = None

        # Feature extractors for different aspects
        self._tile_encoder = None
        self._structure_encoder = None
        self._feature_encoder = None

    def _generate_embedding_id(self, region_id: str, vector: List[float]) -> str:
        """Generate unique embedding ID."""
        content = f"{region_id}_{len(vector)}_{sum(vector[:10]):.4f}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:16]

    def _extract_tile_features(self, region_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from tile composition.

        Features include:
        - Ground type distribution
        - Item density
        - Walkability ratio
        - Obstacle patterns
        """
        tiles = region_data.get("tiles", [])
        features = np.zeros(32)

        if not tiles:
            return features

        ground_types = {}
        item_counts = []
        walkable = 0
        blocked = 0

        for tile in tiles:
            ground = tile.get("ground", "unknown")
            ground_types[ground] = ground_types.get(ground, 0) + 1

            items = tile.get("items", [])
            item_counts.append(len(items))

            # Check walkability
            if tile.get("walkable", True):
                walkable += 1
            else:
                blocked += 1

        total_tiles = len(tiles)

        # Ground type distribution (first 16 features)
        sorted_grounds = sorted(ground_types.items(), key=lambda x: x[1], reverse=True)
        for i, (ground, count) in enumerate(sorted_grounds[:16]):
            features[i] = count / total_tiles

        # Item density statistics (features 16-19)
        if item_counts:
            features[16] = np.mean(item_counts)
            features[17] = np.std(item_counts)
            features[18] = np.max(item_counts)
            features[19] = np.min(item_counts)

        # Walkability ratio (feature 20)
        features[20] = walkable / total_tiles if total_tiles > 0 else 0

        # Blocked ratio (feature 21)
        features[21] = blocked / total_tiles if total_tiles > 0 else 0

        # Tile count features (features 22-25)
        features[22] = min(total_tiles / 1000, 1.0)  # Normalized tile count
        features[23] = len(ground_types)  # Ground diversity
        features[24] = (
            max(ground_types.values()) / total_tiles if total_tiles > 0 else 0
        )
        features[25] = (
            sum(1 for c in ground_types.values() if c == 1) / len(ground_types)
            if ground_types
            else 0
        )

        return features

    def _extract_structure_features(self, region_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract structural features from the region.

        Features include:
        - Room count and sizes
        - Corridor patterns
        - Connectivity metrics
        - Spatial distribution
        """
        features = np.zeros(32)

        rooms = region_data.get("rooms", [])
        corridors = region_data.get("corridors", [])
        connections = region_data.get("connections", [])

        # Room statistics (features 0-7)
        if rooms:
            room_sizes = [r.get("area", 0) for r in rooms]
            features[0] = len(rooms)
            features[1] = np.mean(room_sizes)
            features[2] = np.std(room_sizes)
            features[3] = np.max(room_sizes)
            features[4] = np.min(room_sizes)
            features[5] = sum(
                1 for r in rooms if r.get("shape") == "rectangular"
            ) / len(rooms)
            features[6] = sum(1 for r in rooms if r.get("shape") == "irregular") / len(
                rooms
            )
            features[7] = sum(r.get("doors", 0) for r in rooms) / len(rooms)

        # Corridor statistics (features 8-11)
        if corridors:
            corridor_lengths = [c.get("length", 0) for c in corridors]
            features[8] = len(corridors)
            features[9] = np.mean(corridor_lengths)
            features[10] = np.std(corridor_lengths)
            features[11] = max(corridor_lengths)

        # Connectivity metrics (features 12-19)
        if connections:
            features[12] = len(connections)
            features[13] = len(set(c.get("from") for c in connections))
            features[14] = len(set(c.get("to") for c in connections))
            features[15] = len(connections) / max(len(rooms), 1)  # Connections per room

        # Spatial distribution (features 16-23)
        bounds = region_data.get("bounds", {})
        if bounds:
            width = bounds.get("width", 0)
            height = bounds.get("height", 0)
            features[16] = width
            features[17] = height
            features[18] = width / height if height > 0 else 0  # Aspect ratio
            features[19] = width * height  # Total area

        # Density features (features 20-23)
        total_area = features[19] if features[19] > 0 else 1
        features[20] = sum(room_sizes) / total_area if rooms and total_area > 0 else 0
        features[21] = len(rooms) / total_area if total_area > 0 else 0
        features[22] = len(corridors) / total_area if total_area > 0 else 0

        return features

    def _extract_feature_features(self, region_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from special elements in the region.

        Features include:
        - Spawn points
        - NPCs
        - Special items
        - Environmental effects
        """
        features = np.zeros(32)

        spawns = region_data.get("spawns", [])
        npcs = region_data.get("npcs", [])
        special_items = region_data.get("special_items", [])
        effects = region_data.get("effects", [])

        # Spawn statistics (features 0-7)
        if spawns:
            features[0] = len(spawns)
            monster_types = set(s.get("monster_type", "") for s in spawns)
            features[1] = len(monster_types)
            spawn_sizes = [s.get("radius", 0) for s in spawns]
            features[2] = np.mean(spawn_sizes)
            features[3] = np.max(spawn_sizes)
            features[4] = sum(s.get("interval", 0) for s in spawns) / len(spawns)

        # NPC statistics (features 8-11)
        if npcs:
            features[8] = len(npcs)
            npc_types = set(n.get("type", "") for n in npcs)
            features[9] = len(npc_types)

        # Special items (features 12-19)
        if special_items:
            features[12] = len(special_items)
            item_types = {}
            for item in special_items:
                item_type = item.get("type", "unknown")
                item_types[item_type] = item_types.get(item_type, 0) + 1
            features[13] = len(item_types)
            features[14] = max(item_types.values())

        # Environmental effects (features 20-23)
        if effects:
            features[20] = len(effects)
            effect_types = set(e.get("type", "") for e in effects)
            features[21] = len(effect_types)

        return features

    def _extract_style_features(self, region_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract style-specific features.

        Features capture the architectural style characteristics
        that distinguish different map styles (Issavi, Roshamuul, etc.)
        """
        features = np.zeros(32)

        style = region_data.get("style", "unknown")
        ground_types = region_data.get("ground_types", {})
        region_data.get("wall_types", {})

        # Style encoding (one-hot-like, features 0-7)
        style_map = {
            "issavi": 0,
            "roshamuul": 1,
            "soulwar": 2,
            "library": 3,
            "falcon": 4,
            "cobra": 5,
            "yalahar": 6,
            "thais": 7,
        }
        if style in style_map:
            features[style_map[style]] = 1.0

        # Ground type style indicators (features 8-15)
        style_grounds = {
            "issavi": ["sand", "ancient_stone", "desert_tile"],
            "roshamuul": ["roshamuul_stone", "prison_wall", "dark_tile"],
            "soulwar": ["soul_stone", "war_stone", "spirit_tile"],
            "library": ["library_floor", "bookshelf", "study_tile"],
            "falcon": ["falcon_tile", "bird_motif", "eagle_symbol"],
            "cobra": ["cobra_tile", "serpent_motif", "snake_symbol"],
        }

        for style_name, grounds in style_grounds.items():
            style_score = sum(ground_types.get(g, 0) for g in grounds)
            total = sum(ground_types.values()) if ground_types else 1
            idx = 8 + list(style_grounds.keys()).index(style_name)
            if idx < 16:
                features[idx] = style_score / total

        return features

    def embed_region(self, region_data: Dict[str, Any]) -> MapEmbedding:
        """
        Generate embedding for a single region.

        Args:
            region_data: Dictionary containing region data

        Returns:
            MapEmbedding object
        """
        # Extract feature vectors
        tile_features = self._extract_tile_features(region_data)
        structure_features = self._extract_structure_features(region_data)
        feature_features = self._extract_feature_features(region_data)
        style_features = self._extract_style_features(region_data)

        # Concatenate all features
        combined = np.concatenate(
            [tile_features, structure_features, feature_features, style_features]
        )

        # Pad or truncate to target dimensions
        current_dim = len(combined)
        if current_dim < self.dimensions:
            padding = np.zeros(self.dimensions - current_dim)
            combined = np.concatenate([combined, padding])
        elif current_dim > self.dimensions:
            combined = combined[: self.dimensions]

        # Normalize
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm

        # Create embedding
        region_id = region_data.get("region_id", "unknown")
        embedding = MapEmbedding(
            embedding_id=self._generate_embedding_id(region_id, combined.tolist()),
            region_id=region_id,
            region_type=region_data.get("region_type", "unknown"),
            style=region_data.get("style"),
            vector=combined.tolist(),
            dimensions=self.dimensions,
            metadata={
                "tile_features_norm": float(np.linalg.norm(tile_features)),
                "structure_features_norm": float(np.linalg.norm(structure_features)),
                "feature_features_norm": float(np.linalg.norm(feature_features)),
                "style_features_norm": float(np.linalg.norm(style_features)),
            },
        )

        return embedding

    def embed_regions(self, regions: List[Dict[str, Any]]) -> List[MapEmbedding]:
        """
        Generate embeddings for multiple regions.

        Args:
            regions: List of region data dictionaries

        Returns:
            List of MapEmbedding objects
        """
        return [self.embed_region(r) for r in regions]

    def embed_dataset(self, dataset: Dict[str, Any]) -> List[MapEmbedding]:
        """
        Generate embeddings for all regions in a dataset.

        Args:
            dataset: Dataset dictionary from DatasetBuilder

        Returns:
            List of MapEmbedding objects
        """
        regions = dataset.get("regions", [])
        return self.embed_regions(regions)

    def similarity(self, embedding1: MapEmbedding, embedding2: MapEmbedding) -> float:
        """
        Compute similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1, higher = more similar)
        """
        v1 = np.array(embedding1.vector)
        v2 = np.array(embedding2.vector)

        # Cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float((similarity + 1) / 2)  # Normalize to 0-1

    def get_type_embedding(self, region_type: str) -> str:
        """Get recommended embedding dimensions for a region type."""
        return self.TYPE_DIMENSIONS.get(region_type, self.TYPE_DIMENSIONS["default"])

    def save_embeddings(self, embeddings: List[MapEmbedding], output_path: str):
        """Save embeddings to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = {
            "version": "1.0",
            "dimensions": self.dimensions,
            "count": len(embeddings),
            "embeddings": [e.to_dict() for e in embeddings],
        }
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_embeddings(self, input_path: str) -> List[MapEmbedding]:
        """Load embeddings from file."""
        with open(input_path, "r") as f:
            data = json.load(f)
        return [MapEmbedding.from_dict(e) for e in data.get("embeddings", [])]
