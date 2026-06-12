"""
Pattern Encoder - Learns and encodes structural patterns from OpenTibia maps.

This module focuses on learning architectural patterns including layout,
connectivity, density, and overall architecture of map regions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
import json
import os
from collections import Counter, defaultdict
import math


@dataclass
class PatternProfile:
    """Represents a learned architectural pattern."""

    pattern_id: str
    pattern_type: str  # layout, connectivity, density, architecture

    # Layout patterns
    room_arrangement: str  # grid, linear, radial, organic, clustered
    symmetry_score: float
    axial_alignment: float

    # Connectivity patterns
    avg_degree: float  # Average connections per node
    clustering_coefficient: float
    path_length_avg: float
    bottleneck_count: int

    # Density patterns
    tile_density: float
    feature_density: float
    empty_space_ratio: float
    wall_ratio: float

    # Architecture patterns
    complexity_score: float
    repetition_score: float
    hierarchy_depth: int
    modularity_score: float

    # Sample count
    sample_count: int

    # Pattern vector
    pattern_vector: List[float]


class PatternEncoder:
    """
    Encodes and learns architectural patterns from map data.

    The encoder analyzes map regions to identify recurring patterns
    in layout, connectivity, density, and overall architecture.
    """

    # Pattern types
    PATTERN_TYPES = ["layout", "connectivity", "density", "architecture"]

    # Layout patterns
    LAYOUT_TYPES = [
        "grid",
        "linear",
        "radial",
        "organic",
        "clustered",
        "spiral",
        "branching",
        "hierarchical",
    ]

    def __init__(self, pattern_types: List[str] = None):
        """
        Initialize the pattern encoder.

        Args:
            pattern_types: Optional list of pattern types to focus on
        """
        self.pattern_types = pattern_types or self.PATTERN_TYPES
        self.pattern_profiles: Dict[str, PatternProfile] = {}
        self.layout_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.connectivity_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.density_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.architecture_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._trained = False

    def _compute_grid_score(self, rooms: List[Dict[str, Any]]) -> float:
        """
        Compute how grid-like the room arrangement is.

        Returns a score between 0 and 1, where 1 is perfect grid.
        """
        if len(rooms) < 4:
            return 0.0

        # Check for aligned positions
        x_positions = [r.get("x", 0) for r in rooms]
        y_positions = [r.get("y", 0) for r in rooms]

        # Count unique x and y positions
        unique_x = len(set(x_positions))
        unique_y = len(set(y_positions))

        # Perfect grid would have sqrt(n) unique positions in each dimension
        n = len(rooms)
        expected = math.sqrt(n)

        x_score = 1.0 - abs(unique_x - expected) / max(expected, 1)
        y_score = 1.0 - abs(unique_y - expected) / max(expected, 1)

        return max(0, min(1, (x_score + y_score) / 2))

    def _compute_linearity_score(self, rooms: List[Dict[str, Any]]) -> float:
        """
        Compute how linear the room arrangement is.

        Returns a score between 0 and 1, where 1 is perfectly linear.
        """
        if len(rooms) < 3:
            return 0.0

        # Sort rooms by x position
        sorted_rooms = sorted(rooms, key=lambda r: r.get("x", 0))

        # Check if y positions are relatively constant
        y_values = [r.get("y", 0) for r in sorted_rooms]
        y_variance = np.var(y_values)

        # Normalize variance
        max_y = max(y_values) - min(y_values) if y_values else 1
        normalized_variance = y_variance / max(max_y**2, 1)

        return max(0, 1.0 - normalized_variance)

    def _compute_radial_score(self, rooms: List[Dict[str, Any]]) -> float:
        """
        Compute how radial the room arrangement is.

        Returns a score between 0 and 1, where 1 is perfectly radial.
        """
        if len(rooms) < 4:
            return 0.0

        # Find center
        center_x = np.mean([r.get("x", 0) for r in rooms])
        center_y = np.mean([r.get("y", 0) for r in rooms])

        # Compute distances from center
        distances = []
        angles = []
        for room in rooms:
            dx = room.get("x", 0) - center_x
            dy = room.get("y", 0) - center_y
            dist = math.sqrt(dx**2 + dy**2)
            angle = math.atan2(dy, dx)
            distances.append(dist)
            angles.append(angle)

        # Check if distances are similar (rooms on a circle)
        dist_variance = np.var(distances)
        normalized_dist_var = dist_variance / max(np.mean(distances) ** 2, 1)

        # Check if angles are evenly distributed
        sorted_angles = sorted(angles)
        angle_diffs = [
            sorted_angles[i + 1] - sorted_angles[i]
            for i in range(len(sorted_angles) - 1)
        ]
        if angle_diffs:
            angle_variance = np.var(angle_diffs)
            normalized_angle_var = angle_variance / max(np.mean(angle_diffs) ** 2, 1)
        else:
            normalized_angle_var = 1.0

        return max(0, 1.0 - (normalized_dist_var + normalized_angle_var) / 2)

    def _compute_connectivity_metrics(
        self, connections: List[Dict[str, Any]], rooms: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Compute connectivity metrics for a region."""
        if not rooms:
            return {
                "avg_degree": 0,
                "clustering_coefficient": 0,
                "path_length_avg": 0,
                "bottleneck_count": 0,
            }

        # Build adjacency list
        adjacency = defaultdict(set)
        for conn in connections:
            from_id = conn.get("from")
            to_id = conn.get("to")
            adjacency[from_id].add(to_id)
            adjacency[to_id].add(from_id)

        n = len(rooms)

        # Average degree
        degrees = [
            len(adjacency.get(r.get("id", i), set())) for i, r in enumerate(rooms)
        ]
        avg_degree = np.mean(degrees) if degrees else 0

        # Clustering coefficient
        clustering_coeffs = []
        for room in rooms:
            room_id = room.get("id", "")
            neighbors = adjacency.get(room_id, set())
            if len(neighbors) < 2:
                clustering_coeffs.append(0)
                continue

            # Count connections between neighbors
            neighbor_list = list(neighbors)
            possible_connections = len(neighbor_list) * (len(neighbor_list) - 1) / 2
            actual_connections = 0

            for i, n1 in enumerate(neighbor_list):
                for n2 in neighbor_list[i + 1 :]:
                    if n2 in adjacency.get(n1, set()):
                        actual_connections += 1

            coeff = actual_connections / max(possible_connections, 1)
            clustering_coeffs.append(coeff)

        clustering_coefficient = np.mean(clustering_coeffs) if clustering_coeffs else 0

        # Average shortest path length (simplified)
        path_lengths = []
        for i, room1 in enumerate(rooms[:10]):  # Limit for performance
            for j, room2 in enumerate(rooms[i + 1 : 10]):
                # BFS to find shortest path
                path_length = self._bfs_shortest_path(
                    adjacency, room1.get("id", ""), room2.get("id", "")
                )
                if path_length > 0:
                    path_lengths.append(path_length)

        path_length_avg = np.mean(path_lengths) if path_lengths else 0

        # Bottleneck detection (rooms with high betweenness)
        bottleneck_count = 0
        for room in rooms:
            room_id = room.get("id", "")
            degree = len(adjacency.get(room_id, set()))
            if degree <= 1 and n > 3:  # Potential bottleneck
                bottleneck_count += 1

        return {
            "avg_degree": avg_degree,
            "clustering_coefficient": clustering_coefficient,
            "path_length_avg": path_length_avg,
            "bottleneck_count": bottleneck_count,
        }

    def _bfs_shortest_path(
        self, adjacency: Dict[str, Set[str]], start: str, end: str
    ) -> int:
        """Find shortest path using BFS."""
        if start == end:
            return 0

        visited = {start}
        queue = [(start, 0)]

        while queue:
            current, dist = queue.pop(0)
            for neighbor in adjacency.get(current, set()):
                if neighbor == end:
                    return dist + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        return -1  # No path

    def _compute_density_metrics(self, region_data: Dict[str, Any]) -> Dict[str, float]:
        """Compute density metrics for a region."""
        tiles = region_data.get("tiles", [])
        bounds = region_data.get("bounds", {})

        if not tiles or not bounds:
            return {
                "tile_density": 0,
                "feature_density": 0,
                "empty_space_ratio": 1,
                "wall_ratio": 0,
            }

        total_area = bounds.get("width", 1) * bounds.get("height", 1)
        tile_count = len(tiles)

        # Tile density
        tile_density = tile_count / max(total_area, 1)

        # Feature density
        feature_count = 0
        wall_count = 0
        for tile in tiles:
            items = tile.get("items", [])
            feature_count += len(items)
            for item in items:
                if "wall" in item.get("type", "").lower():
                    wall_count += 1

        feature_density = feature_count / max(tile_count, 1)

        # Empty space ratio
        occupied_area = tile_count  # Assume each tile occupies 1 unit
        empty_space_ratio = 1.0 - (occupied_area / max(total_area, 1))

        # Wall ratio
        wall_ratio = wall_count / max(feature_count, 1)

        return {
            "tile_density": tile_density,
            "feature_density": feature_density,
            "empty_space_ratio": max(0, empty_space_ratio),
            "wall_ratio": wall_ratio,
        }

    def _compute_architecture_metrics(
        self, region_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute overall architecture metrics for a region."""
        rooms = region_data.get("rooms", [])
        corridors = region_data.get("corridors", [])
        tiles = region_data.get("tiles", [])

        # Complexity score (based on variety of elements)
        ground_types = set(t.get("ground", "") for t in tiles)
        item_types = set()
        for tile in tiles:
            for item in tile.get("items", []):
                item_types.add(item.get("type", ""))

        complexity = (len(ground_types) + len(item_types)) / max(len(tiles), 1) * 10

        # Repetition score (how much patterns repeat)
        if rooms:
            room_sizes = [r.get("area", 0) for r in rooms]
            size_variance = np.var(room_sizes)
            avg_size = np.mean(room_sizes)
            repetition = 1.0 - min(size_variance / max(avg_size**2, 1), 1)
        else:
            repetition = 0.5

        # Hierarchy depth (levels of organization)
        hierarchy_depth = 1  # At least the region itself
        if rooms:
            hierarchy_depth += 1
            for room in rooms:
                if room.get("subrooms"):
                    hierarchy_depth += 1
                    break

        # Modularity score (how separable the regions are)
        if rooms and corridors:
            modularity = len(rooms) / max(len(rooms) + len(corridors), 1)
        else:
            modularity = 0.5

        return {
            "complexity_score": min(complexity, 1),
            "repetition_score": repetition,
            "hierarchy_depth": hierarchy_depth,
            "modularity_score": modularity,
        }

    def _determine_layout_type(self, region_data: Dict[str, Any]) -> str:
        """Determine the dominant layout type for a region."""
        rooms = region_data.get("rooms", [])

        if len(rooms) < 3:
            return "organic"

        grid_score = self._compute_grid_score(rooms)
        linear_score = self._compute_linearity_score(rooms)
        radial_score = self._compute_radial_score(rooms)

        scores = {"grid": grid_score, "linear": linear_score, "radial": radial_score}

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        if best_score < 0.5:
            return "organic"

        return best_type

    def extract_pattern(self, region_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all pattern features from a region.

        Args:
            region_data: Region data dictionary

        Returns:
            Dictionary of pattern features
        """
        rooms = region_data.get("rooms", [])
        connections = region_data.get("connections", [])

        # Layout patterns
        layout_type = self._determine_layout_type(region_data)
        grid_score = self._compute_grid_score(rooms)
        linear_score = self._compute_linearity_score(rooms)
        radial_score = self._compute_radial_score(rooms)

        # Compute symmetry
        if rooms:
            x_positions = [r.get("x", 0) for r in rooms]
            y_positions = [r.get("y", 0) for r in rooms]
            symmetry_score = 1.0 - (np.var(x_positions) + np.var(y_positions)) / 100
            symmetry_score = max(0, min(1, symmetry_score))
        else:
            symmetry_score = 0

        # Axial alignment
        axial_alignment = max(grid_score, linear_score)

        # Connectivity patterns
        conn_metrics = self._compute_connectivity_metrics(connections, rooms)

        # Density patterns
        density_metrics = self._compute_density_metrics(region_data)

        # Architecture patterns
        arch_metrics = self._compute_architecture_metrics(region_data)

        return {
            "layout_type": layout_type,
            "grid_score": grid_score,
            "linear_score": linear_score,
            "radial_score": radial_score,
            "symmetry_score": symmetry_score,
            "axial_alignment": axial_alignment,
            "avg_degree": conn_metrics["avg_degree"],
            "clustering_coefficient": conn_metrics["clustering_coefficient"],
            "path_length_avg": conn_metrics["path_length_avg"],
            "bottleneck_count": conn_metrics["bottleneck_count"],
            "tile_density": density_metrics["tile_density"],
            "feature_density": density_metrics["feature_density"],
            "empty_space_ratio": density_metrics["empty_space_ratio"],
            "wall_ratio": density_metrics["wall_ratio"],
            "complexity_score": arch_metrics["complexity_score"],
            "repetition_score": arch_metrics["repetition_score"],
            "hierarchy_depth": arch_metrics["hierarchy_depth"],
            "modularity_score": arch_metrics["modularity_score"],
        }

    def add_sample(self, pattern_type: str, region_data: Dict[str, Any]):
        """
        Add a sample region to a pattern type's training data.

        Args:
            pattern_type: Type of pattern (layout, connectivity, density, architecture)
            region_data: Region data dictionary
        """
        pattern_dict = {
            "layout": self.layout_patterns,
            "connectivity": self.connectivity_patterns,
            "density": self.density_patterns,
            "architecture": self.architecture_patterns,
        }

        if pattern_type in pattern_dict:
            pattern_dict[pattern_type][pattern_type].append(region_data)
        self._trained = False

    def train(self, dataset: Dict[str, Any] = None):
        """
        Train the pattern encoder on a dataset.

        Args:
            dataset: Dataset dictionary from DatasetBuilder
        """
        if dataset:
            regions = dataset.get("regions", [])
            for region in regions:
                for pattern_type in self.pattern_types:
                    self.add_sample(pattern_type, region)

        # Build pattern profiles
        for pattern_type in self.pattern_types:
            samples = getattr(self, f"{pattern_type}_patterns").get(pattern_type, [])
            if samples:
                self.pattern_profiles[pattern_type] = self._build_pattern_profile(
                    pattern_type, samples
                )

        self._trained = True

    def _build_pattern_profile(
        self, pattern_type: str, samples: List[Dict[str, Any]]
    ) -> PatternProfile:
        """Build a pattern profile from samples."""
        # Extract patterns from all samples
        all_patterns = []
        for sample in samples:
            pattern = self.extract_pattern(sample)
            all_patterns.append(pattern)

        # Aggregate metrics
        layout_types = Counter(p["layout_type"] for p in all_patterns)

        avg_grid = np.mean([p["grid_score"] for p in all_patterns])
        avg_linear = np.mean([p["linear_score"] for p in all_patterns])
        avg_radial = np.mean([p["radial_score"] for p in all_patterns])
        avg_symmetry = np.mean([p["symmetry_score"] for p in all_patterns])
        avg_axial = np.mean([p["axial_alignment"] for p in all_patterns])

        avg_degree = np.mean([p["avg_degree"] for p in all_patterns])
        avg_clustering = np.mean([p["clustering_coefficient"] for p in all_patterns])
        avg_path = np.mean([p["path_length_avg"] for p in all_patterns])
        total_bottlenecks = int(sum(p["bottleneck_count"] for p in all_patterns))

        avg_tile_density = np.mean([p["tile_density"] for p in all_patterns])
        avg_feature_density = np.mean([p["feature_density"] for p in all_patterns])
        avg_empty_ratio = np.mean([p["empty_space_ratio"] for p in all_patterns])
        avg_wall_ratio = np.mean([p["wall_ratio"] for p in all_patterns])

        avg_complexity = np.mean([p["complexity_score"] for p in all_patterns])
        avg_repetition = np.mean([p["repetition_score"] for p in all_patterns])
        avg_hierarchy = int(np.mean([p["hierarchy_depth"] for p in all_patterns]))
        avg_modularity = np.mean([p["modularity_score"] for p in all_patterns])

        # Create pattern vector
        pattern_vector = [
            avg_grid,
            avg_linear,
            avg_radial,
            avg_symmetry,
            avg_axial,
            avg_degree,
            avg_clustering,
            avg_path,
            avg_tile_density,
            avg_feature_density,
            avg_empty_ratio,
            avg_wall_ratio,
            avg_complexity,
            avg_repetition,
            avg_hierarchy,
            avg_modularity,
        ]

        # Generate pattern ID
        pattern_id = f"pattern_{pattern_type}_{len(samples)}"

        # Determine dominant layout
        dominant_layout = (
            layout_types.most_common(1)[0][0] if layout_types else "organic"
        )

        return PatternProfile(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            room_arrangement=dominant_layout,
            symmetry_score=avg_symmetry,
            axial_alignment=avg_axial,
            avg_degree=avg_degree,
            clustering_coefficient=avg_clustering,
            path_length_avg=avg_path,
            bottleneck_count=total_bottlenecks,
            tile_density=avg_tile_density,
            feature_density=avg_feature_density,
            empty_space_ratio=avg_empty_ratio,
            wall_ratio=avg_wall_ratio,
            complexity_score=avg_complexity,
            repetition_score=avg_repetition,
            hierarchy_depth=avg_hierarchy,
            modularity_score=avg_modularity,
            sample_count=len(samples),
            pattern_vector=pattern_vector,
        )

    def classify_layout(self, region_data: Dict[str, Any]) -> Tuple[str, float]:
        """
        Classify the layout type of a region.

        Args:
            region_data: Region data to classify

        Returns:
            Tuple of (layout_type, confidence)
        """
        pattern = self.extract_pattern(region_data)

        layout_type = pattern["layout_type"]

        # Calculate confidence based on score strength
        if layout_type == "grid":
            confidence = pattern["grid_score"]
        elif layout_type == "linear":
            confidence = pattern["linear_score"]
        elif layout_type == "radial":
            confidence = pattern["radial_score"]
        else:
            confidence = 0.5

        return (layout_type, confidence)

    def get_pattern_profile(self, pattern_type: str) -> Optional[PatternProfile]:
        """Get the profile for a specific pattern type."""
        return self.pattern_profiles.get(pattern_type)

    def generate_pattern_guide(self, pattern_type: str = None) -> Dict[str, Any]:
        """
        Generate a pattern guide for map generation.

        Args:
            pattern_type: Optional specific pattern type

        Returns:
            Pattern guide dictionary for use in map generation
        """
        guides = {}

        for ptype in self.pattern_types:
            profile = self.pattern_profiles.get(ptype)
            if not profile:
                continue

            guides[ptype] = {
                "pattern_type": ptype,
                "room_arrangement": profile.room_arrangement,
                "symmetry_score": profile.symmetry_score,
                "axial_alignment": profile.axial_alignment,
                "avg_degree": profile.avg_degree,
                "clustering_coefficient": profile.clustering_coefficient,
                "target_tile_density": profile.tile_density,
                "target_feature_density": profile.feature_density,
                "complexity_score": profile.complexity_score,
                "modularity_score": profile.modularity_score,
            }

        if pattern_type:
            return guides.get(pattern_type, {})

        return guides

    def compare_patterns(
        self, region1: Dict[str, Any], region2: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Compare patterns between two regions.

        Args:
            region1: First region data
            region2: Second region data

        Returns:
            Dictionary of similarity scores for each pattern aspect
        """
        pattern1 = self.extract_pattern(region1)
        pattern2 = self.extract_pattern(region2)

        similarities = {}

        # Layout similarity
        if pattern1["layout_type"] == pattern2["layout_type"]:
            similarities["layout"] = 1.0
        else:
            similarities["layout"] = 0.3

        # Numeric feature similarities
        numeric_features = [
            "symmetry_score",
            "axial_alignment",
            "avg_degree",
            "clustering_coefficient",
            "tile_density",
            "feature_density",
            "complexity_score",
            "modularity_score",
        ]

        for feature in numeric_features:
            val1 = pattern1.get(feature, 0)
            val2 = pattern2.get(feature, 0)
            diff = abs(val1 - val2)
            similarities[feature] = max(0, 1.0 - diff)

        return similarities

    def save_profiles(self, output_path: str):
        """Save pattern profiles to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = {"version": "1.0", "pattern_types": self.pattern_types, "profiles": {}}

        for ptype, profile in self.pattern_profiles.items():
            data["profiles"][ptype] = asdict(profile)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_profiles(self, input_path: str):
        """Load pattern profiles from file."""
        with open(input_path, "r") as f:
            data = json.load(f)

        self.pattern_types = data.get("pattern_types", self.PATTERN_TYPES)
        self.pattern_profiles = {}

        for ptype, profile_data in data.get("profiles", {}).items():
            self.pattern_profiles[ptype] = PatternProfile(**profile_data)

        self._trained = True

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about learned patterns."""
        stats = {}
        for ptype, profile in self.pattern_profiles.items():
            stats[ptype] = {
                "sample_count": profile.sample_count,
                "room_arrangement": profile.room_arrangement,
                "symmetry_score": profile.symmetry_score,
                "avg_degree": profile.avg_degree,
                "tile_density": profile.tile_density,
                "complexity_score": profile.complexity_score,
            }
        return stats
