"""
Learning Pipeline - Orchestrates continuous learning from OpenTibia maps.

This module provides the main pipeline for learning from maps, generating
blueprints, and continuously improving map generation quality.
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from collections import defaultdict
import hashlib


@dataclass
class LearningConfig:
    """Configuration for the learning pipeline."""
    maps_directory: str = "maps"
    dataset_path: str = "data/dataset.json"
    embeddings_path: str = "data/embeddings.json"
    style_profiles_path: str = "data/style_profiles.json"
    pattern_profiles_path: str = "data/pattern_profiles.json"
    similarity_index_path: str = "data/similarity_index.json"
    blueprints_path: str = "data/blueprints"
    
    # Learning parameters
    embedding_dimensions: int = 128
    min_samples_per_style: int = 5
    similarity_threshold: float = 0.7
    
    # Generation parameters
    blueprint_count: int = 10
    variation_factor: float = 0.2
    
    # Continuous learning
    auto_retrain: bool = True
    retrain_interval_hours: int = 24
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningConfig":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class LearningMetrics:
    """Metrics from a learning iteration."""
    timestamp: str
    maps_processed: int
    regions_extracted: int
    styles_learned: int
    patterns_learned: int
    embeddings_generated: int
    training_time_seconds: float
    quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class GeneratedBlueprint:
    """A generated map blueprint from learned patterns."""
    blueprint_id: str
    style: str
    region_type: str
    layout_pattern: str
    rooms: List[Dict[str, Any]]
    corridors: List[Dict[str, Any]]
    features: List[Dict[str, Any]]
    ground_distribution: Dict[str, float]
    wall_distribution: Dict[str, float]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class LearningPipeline:
    """
    Main pipeline for continuous map learning.
    
    The pipeline orchestrates the entire learning process:
    1. Dataset building from raw map files
    2. Embedding generation
    3. Style learning
    4. Pattern learning
    5. Similarity index building
    6. Blueprint generation
    """
    
    def __init__(self, config: LearningConfig = None):
        """
        Initialize the learning pipeline.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config or LearningConfig()
        
        # Components (initialized during training)
        self.dataset_builder = None
        self.map_embedder = None
        self.style_encoder = None
        self.pattern_encoder = None
        self.similarity_engine = None
        
        # State
        self.dataset = None
        self.embeddings = []
        self._trained = False
        self._last_training = None
        self._metrics_history: List[LearningMetrics] = []
        
    def _import_components(self):
        """Import pipeline components."""
        from .dataset_builder import DatasetBuilder
        from .map_embedding import MapEmbedder
        from .style_encoder import StyleEncoder
        from .pattern_encoder import PatternEncoder
        from .similarity_engine import SimilarityEngine
        
        self.dataset_builder = DatasetBuilder(self.config.maps_directory)
        self.map_embedder = MapEmbedder(dimensions=self.config.embedding_dimensions)
        self.style_encoder = StyleEncoder()
        self.pattern_encoder = PatternEncoder()
        self.similarity_engine = SimilarityEngine(self.config.similarity_index_path)
        
    def train(self, dataset: Dict[str, Any] = None) -> LearningMetrics:
        """
        Run the full training pipeline.
        
        Args:
            dataset: Optional pre-built dataset (skips dataset building)
            
        Returns:
            LearningMetrics from this training iteration
        """
        start_time = time.time()
        
        # Import components if not already done
        if self.dataset_builder is None:
            self._import_components()
            
        # Step 1: Build or use provided dataset
        if dataset is None:
            print("Building dataset...")
            self.dataset = self.dataset_builder.build_dataset(self.config.dataset_path)
        else:
            self.dataset = dataset
            
        maps_processed = self.dataset.get("statistics", {}).get("total_files", 0)
        regions_extracted = len(self.dataset.get("regions", []))
        
        # Step 2: Generate embeddings
        print("Generating embeddings...")
        self.embeddings = self.map_embedder.embed_dataset(self.dataset)
        self.map_embedder.save_embeddings(self.embeddings, self.config.embeddings_path)
        embeddings_generated = len(self.embeddings)
        
        # Step 3: Train style encoder
        print("Training style encoder...")
        self.style_encoder.train(self.dataset)
        self.style_encoder.save_profiles(self.config.style_profiles_path)
        styles_learned = len(self.style_encoder.style_profiles)
        
        # Step 4: Train pattern encoder
        print("Training pattern encoder...")
        self.pattern_encoder.train(self.dataset)
        self.pattern_encoder.save_profiles(self.config.pattern_profiles_path)
        patterns_learned = len(self.pattern_encoder.pattern_profiles)
        
        # Step 5: Build similarity index
        print("Building similarity index...")
        region_data = {r.get("region_id", str(i)): r for i, r in 
                      enumerate(self.dataset.get("regions", []))}
        self.similarity_engine.build_index(
            self.embeddings,
            self.style_encoder,
            self.pattern_encoder,
            region_data
        )
        self.similarity_engine.save_index(self.config.similarity_index_path)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score()
        
        training_time = time.time() - start_time
        
        # Create metrics
        metrics = LearningMetrics(
            timestamp=datetime.now().isoformat(),
            maps_processed=maps_processed,
            regions_extracted=regions_extracted,
            styles_learned=styles_learned,
            patterns_learned=patterns_learned,
            embeddings_generated=embeddings_generated,
            training_time_seconds=training_time,
            quality_score=quality_score
        )
        
        self._metrics_history.append(metrics)
        self._trained = True
        self._last_training = datetime.now()
        
        print(f"Training complete! Quality score: {quality_score:.2f}")
        return metrics
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score for the learned models."""
        score = 0.0
        factors = 0
        
        # Factor 1: Dataset size (up to 25 points)
        regions = len(self.dataset.get("regions", []))
        score += min(regions / 100, 1.0) * 25
        factors += 25
        
        # Factor 2: Style coverage (up to 25 points)
        styles = len(self.style_encoder.style_profiles)
        expected_styles = 8  # Known styles
        score += min(styles / expected_styles, 1.0) * 25
        factors += 25
        
        # Factor 3: Pattern coverage (up to 25 points)
        patterns = len(self.pattern_encoder.pattern_profiles)
        expected_patterns = 4
        score += min(patterns / expected_patterns, 1.0) * 25
        factors += 25
        
        # Factor 4: Sample adequacy (up to 25 points)
        adequate_samples = sum(
            1 for profile in self.style_encoder.style_profiles.values()
            if profile.sample_count >= self.config.min_samples_per_style
        )
        score += (adequate_samples / max(styles, 1)) * 25
        factors += 25
        
        return score
    
    def find_similar(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find maps similar to the query.
        
        Args:
            query: Query string (e.g., "Find maps similar to Roshamuul")
            top_k: Number of results
            
        Returns:
            List of similarity results
        """
        if not self._trained:
            raise RuntimeError("Pipeline not trained. Call train() first.")
            
        results = self.similarity_engine.query(query, top_k)
        return [r.to_dict() for r in results]
    
    def generate_blueprint(self, style: str = None, 
                          region_type: str = None,
                          count: int = None) -> List[GeneratedBlueprint]:
        """
        Generate new map blueprints from learned patterns.
        
        Args:
            style: Optional style to generate for
            region_type: Optional region type to generate for
            count: Number of blueprints to generate
            
        Returns:
            List of GeneratedBlueprint objects
        """
        if not self._trained:
            raise RuntimeError("Pipeline not trained. Call train() first.")
            
        count = count or self.config.blueprint_count
        blueprints = []
        
        # Get style guide
        if style:
            style_guide = self.style_encoder.generate_style_guide(style)
        else:
            # Pick a random style
            styles = list(self.style_encoder.style_profiles.keys())
            if styles:
                style = np.random.choice(styles)
                style_guide = self.style_encoder.generate_style_guide(style)
            else:
                style_guide = {}
                
        # Get pattern guide
        pattern_guide = self.pattern_encoder.generate_pattern_guide()
        
        for i in range(count):
            blueprint = self._generate_single_blueprint(
                style, style_guide, pattern_guide, region_type
            )
            blueprints.append(blueprint)
            
        # Save blueprints
        self._save_blueprints(blueprints)
        
        return blueprints
    
    def _generate_single_blueprint(self, style: str, 
                                  style_guide: Dict[str, Any],
                                  pattern_guide: Dict[str, Any],
                                  region_type: str = None) -> GeneratedBlueprint:
        """Generate a single blueprint."""
        # Generate blueprint ID
        blueprint_id = hashlib.md5(
            f"{style}_{time.time()}_{np.random.rand()}".encode()
        ).hexdigest()[:12]
        
        # Determine region type
        if not region_type:
            types = ["dungeon", "city", "cave", "temple", "tower"]
            region_type = np.random.choice(types)
            
        # Generate rooms based on pattern guide
        rooms = self._generate_rooms(style_guide, pattern_guide, region_type)
        
        # Generate corridors
        corridors = self._generate_corridors(rooms, pattern_guide)
        
        # Generate features
        features = self._generate_features(style_guide, rooms)
        
        # Ground and wall distributions
        ground_dist = style_guide.get("recommended_grounds", {})
        if isinstance(ground_dist, list):
            ground_dist = {g: 1.0/len(ground_dist) for g in ground_dist}
            
        wall_dist = style_guide.get("recommended_walls", {})
        if isinstance(wall_dist, list):
            wall_dist = {w: 1.0/len(wall_dist) for w in wall_dist}
            
        return GeneratedBlueprint(
            blueprint_id=blueprint_id,
            style=style,
            region_type=region_type,
            layout_pattern=pattern_guide.get("room_arrangement", "organic"),
            rooms=rooms,
            corridors=corridors,
            features=features,
            ground_distribution=ground_dist,
            wall_distribution=wall_dist,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "style_guide": style_guide,
                "pattern_guide": pattern_guide
            }
        )
    
    def _generate_rooms(self, style_guide: Dict[str, Any],
                       pattern_guide: Dict[str, Any],
                       region_type: str) -> List[Dict[str, Any]]:
        """Generate rooms for a blueprint."""
        rooms = []
        
        # Determine room count based on region type
        room_count_ranges = {
            "dungeon": (5, 15),
            "city": (10, 30),
            "cave": (3, 10),
            "temple": (2, 8),
            "tower": (3, 12)
        }
        
        min_rooms, max_rooms = room_count_ranges.get(region_type, (3, 10))
        room_count = np.random.randint(min_rooms, max_rooms + 1)
        
        # Get target room size from style guide
        target_size = style_guide.get("avg_room_size", 100)
        variation = self.config.variation_factor
        
        # Generate rooms based on layout pattern
        layout = pattern_guide.get("room_arrangement", "organic")
        
        if layout == "grid":
            rooms = self._generate_grid_rooms(room_count, target_size, variation)
        elif layout == "linear":
            rooms = self._generate_linear_rooms(room_count, target_size, variation)
        elif layout == "radial":
            rooms = self._generate_radial_rooms(room_count, target_size, variation)
        else:
            rooms = self._generate_organic_rooms(room_count, target_size, variation)
            
        return rooms
    
    def _generate_grid_rooms(self, count: int, target_size: float,
                            variation: float) -> List[Dict[str, Any]]:
        """Generate rooms in a grid pattern."""
        rooms = []
        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        
        spacing = target_size ** 0.5 * 2
        
        for i in range(count):
            row = i // cols
            col = i % cols
            
            width = target_size * (1 + np.random.uniform(-variation, variation))
            height = width * np.random.uniform(0.8, 1.2)
            
            rooms.append({
                "id": f"room_{i}",
                "x": col * spacing,
                "y": row * spacing,
                "width": int(width),
                "height": int(height),
                "area": int(width * height),
                "shape": "rectangular"
            })
            
        return rooms
    
    def _generate_linear_rooms(self, count: int, target_size: float,
                              variation: float) -> List[Dict[str, Any]]:
        """Generate rooms in a linear pattern."""
        rooms = []
        spacing = target_size ** 0.5 * 2.5
        
        for i in range(count):
            width = target_size * (1 + np.random.uniform(-variation, variation))
            height = width * np.random.uniform(0.8, 1.2)
            
            rooms.append({
                "id": f"room_{i}",
                "x": i * spacing,
                "y": np.random.uniform(-spacing * 0.2, spacing * 0.2),
                "width": int(width),
                "height": int(height),
                "area": int(width * height),
                "shape": "rectangular"
            })
            
        return rooms
    
    def _generate_radial_rooms(self, count: int, target_size: float,
                              variation: float) -> List[Dict[str, Any]]:
        """Generate rooms in a radial pattern."""
        rooms = []
        center_x, center_y = 0, 0
        radius = target_size ** 0.5 * 2
        
        for i in range(count):
            angle = (2 * np.pi * i) / count + np.random.uniform(-0.2, 0.2)
            r = radius * (1 + np.random.uniform(-variation, variation))
            
            width = target_size * (1 + np.random.uniform(-variation, variation))
            height = width * np.random.uniform(0.8, 1.2)
            
            rooms.append({
                "id": f"room_{i}",
                "x": center_x + r * np.cos(angle),
                "y": center_y + r * np.sin(angle),
                "width": int(width),
                "height": int(height),
                "area": int(width * height),
                "shape": "rectangular"
            })
            
        return rooms
    
    def _generate_organic_rooms(self, count: int, target_size: float,
                               variation: float) -> List[Dict[str, Any]]:
        """Generate rooms in an organic pattern."""
        rooms = []
        x, y = 0, 0
        
        for i in range(count):
            width = target_size * (1 + np.random.uniform(-variation, variation))
            height = width * np.random.uniform(0.6, 1.4)
            
            # Random walk
            if i > 0:
                x += np.random.uniform(-target_size ** 0.5, target_size ** 0.5)
                y += np.random.uniform(-target_size ** 0.5, target_size ** 0.5)
                
            shape_options = ["rectangular", "irregular", "L-shaped"]
            shape = np.random.choice(shape_options, p=[0.5, 0.3, 0.2])
            
            rooms.append({
                "id": f"room_{i}",
                "x": x,
                "y": y,
                "width": int(width),
                "height": int(height),
                "area": int(width * height),
                "shape": shape
            })
            
        return rooms
    
    def _generate_corridors(self, rooms: List[Dict[str, Any]],
                           pattern_guide: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate corridors connecting rooms."""
        corridors = []
        
        if len(rooms) < 2:
            return corridors
            
        # Connect rooms based on proximity
        connectivity = pattern_guide.get("avg_degree", 2)
        
        for i, room in enumerate(rooms):
            # Connect to nearest rooms
            distances = []
            for j, other_room in enumerate(rooms):
                if i != j:
                    dist = ((room["x"] - other_room["x"])**2 + 
                           (room["y"] - other_room["y"])**2)**0.5
                    distances.append((j, dist))
                    
            distances.sort(key=lambda x: x[1])
            
            # Connect to nearest N rooms
            connections = min(int(connectivity), len(distances))
            for j, dist in distances[:connections]:
                corridors.append({
                    "id": f"corridor_{i}_{j}",
                    "from": room["id"],
                    "to": rooms[j]["id"],
                    "length": int(dist),
                    "width": np.random.randint(2, 5)
                })
                
        return corridors
    
    def _generate_features(self, style_guide: Dict[str, Any],
                          rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate features for the blueprint."""
        features = []
        
        decoration_density = style_guide.get("decoration_density", 0.1)
        
        for room in rooms:
            # Add features based on room size and decoration density
            feature_count = max(1, int(room["area"] * decoration_density / 100))
            
            for f in range(feature_count):
                feature_types = ["decoration", "furniture", "light", "container"]
                feature_type = np.random.choice(feature_types)
                
                features.append({
                    "id": f"feature_{room['id']}_{f}",
                    "room_id": room["id"],
                    "type": feature_type,
                    "x": room["x"] + np.random.uniform(0, room["width"]),
                    "y": room["y"] + np.random.uniform(0, room["height"])
                })
                
        return features
    
    def _save_blueprints(self, blueprints: List[GeneratedBlueprint]):
        """Save generated blueprints to files."""
        os.makedirs(self.config.blueprints_path, exist_ok=True)
        
        for blueprint in blueprints:
            filepath = os.path.join(
                self.config.blueprints_path,
                f"blueprint_{blueprint.blueprint_id}.json"
            )
            with open(filepath, 'w') as f:
                json.dump(blueprint.to_dict(), f, indent=2)
                
    def load_trained_models(self):
        """Load previously trained models from disk."""
        self._import_components()
        
        # Load style profiles
        if os.path.exists(self.config.style_profiles_path):
            self.style_encoder.load_profiles(self.config.style_profiles_path)
            
        # Load pattern profiles
        if os.path.exists(self.config.pattern_profiles_path):
            self.pattern_encoder.load_profiles(self.config.pattern_profiles_path)
            
        # Load similarity index
        if os.path.exists(self.config.similarity_index_path):
            self.similarity_engine.load_index(self.config.similarity_index_path)
            
        # Load embeddings
        if os.path.exists(self.config.embeddings_path):
            self.embeddings = self.map_embedder.load_embeddings(
                self.config.embeddings_path)
                
        self._trained = True
        
    def continuous_learning(self, new_maps_directory: str = None) -> LearningMetrics:
        """
        Run continuous learning on new maps.
        
        Args:
            new_maps_directory: Directory with new map files
            
        Returns:
            LearningMetrics from this iteration
        """
        if not self._trained:
            return self.train()
            
        # Build dataset from new maps
        if new_maps_directory:
            old_builder = self.dataset_builder
            self.dataset_builder = type(old_builder)(new_maps_directory)
            new_dataset = self.dataset_builder.build_dataset()
            
            # Merge with existing dataset
            if self.dataset:
                self.dataset["regions"].extend(new_dataset.get("regions", []))
                self.dataset["metadata"].extend(new_dataset.get("metadata", []))
                
        # Retrain
        return self.train(self.dataset)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the learned models."""
        if not self._trained:
            return {"error": "Pipeline not trained"}
            
        stats = {
            "dataset": self.dataset.get("statistics", {}) if self.dataset else {},
            "styles": self.style_encoder.get_style_statistics(),
            "patterns": self.pattern_encoder.get_pattern_statistics(),
            "similarity": {
                "styles": self.similarity_engine.get_style_statistics(),
                "types": self.similarity_engine.get_type_statistics()
            },
            "metrics_history": [m.to_dict() for m in self._metrics_history],
            "quality_score": self._calculate_quality_score()
        }
        
        return stats
    
    def export_for_generation(self, output_path: str = None) -> Dict[str, Any]:
        """
        Export learned data for use in map generation.
        
        Args:
            output_path: Optional path to save the export
            
        Returns:
            Dictionary with all learned data for generation
        """
        if not self._trained:
            return {}
            
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "style_guides": {},
            "pattern_guides": {},
            "similarity_clusters": {}
        }
        
        # Export style guides
        for style in self.style_encoder.list_styles():
            export_data["style_guides"][style] = \
                self.style_encoder.generate_style_guide(style)
                
        # Export pattern guides
        export_data["pattern_guides"] = \
            self.pattern_encoder.generate_pattern_guide()
            
        # Export similarity clusters
        clusters = self.similarity_engine.find_clusters(k=5)
        export_data["similarity_clusters"] = clusters
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
                
        return export_data
    
    def get_recommendations(self, style: str = None, 
                          region_type: str = None) -> Dict[str, Any]:
        """
        Get generation recommendations based on learned patterns.
        
        Args:
            style: Optional style to get recommendations for
            region_type: Optional region type to get recommendations for
            
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            "style_recommendations": [],
            "pattern_recommendations": [],
            "combination_suggestions": []
        }
        
        # Style recommendations
        if style:
            profile = self.style_encoder.get_style_profile(style)
            if profile:
                recommendations["style_recommendations"].append({
                    "style": style,
                    "confidence": profile.sample_count / max(
                        sum(p.sample_count for p in 
                           self.style_encoder.style_profiles.values()), 1),
                    "suggestions": {
                        "ground_tiles": list(profile.ground_preferences.keys())[:5],
                        "wall_tiles": list(profile.wall_preferences.keys())[:5],
                        "avg_room_size": profile.avg_room_size,
                        "decoration_density": profile.decoration_density
                    }
                })
                
        # Pattern recommendations
        for ptype, profile in self.pattern_encoder.pattern_profiles.items():
            recommendations["pattern_recommendations"].append({
                "pattern_type": ptype,
                "room_arrangement": profile.room_arrangement,
                "target_density": profile.tile_density,
                "complexity": profile.complexity_score
            })
            
        # Combination suggestions
        styles = list(self.style_encoder.style_profiles.keys())
        if len(styles) >= 2:
            # Suggest hybrid styles
            for i, style1 in enumerate(styles[:3]):
                for style2 in styles[i+1:4]:
                    recommendations["combination_suggestions"].append({
                        "primary": style1,
                        "secondary": style2,
                        "blend_ratio": "70/30",
                        "compatibility": np.random.uniform(0.5, 0.9)
                    })
                    
        return recommendations