"""
Similarity Engine - Finds and ranks similar maps based on learned embeddings.

This module provides the capability to answer queries like "Find maps similar to Roshamuul"
by comparing embeddings, styles, and patterns across map regions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
import json
import os
from collections import defaultdict
import heapq


@dataclass
class SimilarityResult:
    """Represents a similarity search result."""
    query_id: str
    matched_id: str
    similarity_score: float
    match_type: str  # embedding, style, pattern, hybrid
    matched_region: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SimilarityIndex:
    """Index structure for efficient similarity search."""
    index_id: str
    embeddings: Dict[str, List[float]]
    styles: Dict[str, str]
    patterns: Dict[str, Dict[str, float]]
    metadata: Dict[str, Dict[str, Any]]
    region_data: Dict[str, Dict[str, Any]]


class SimilarityEngine:
    """
    Engine for finding similar maps based on various similarity metrics.
    
    The engine supports multiple similarity search modes:
    - Embedding-based: Using vector similarity
    - Style-based: Using architectural style matching
    - Pattern-based: Using structural pattern matching
    - Hybrid: Combining multiple similarity metrics
    """
    
    # Similarity search modes
    MODE_EMBEDDING = "embedding"
    MODE_STYLE = "style"
    MODE_PATTERN = "pattern"
    MODE_HYBRID = "hybrid"
    
    def __init__(self, index_path: str = None):
        """
        Initialize the similarity engine.
        
        Args:
            index_path: Optional path to load/save index
        """
        self.index_path = index_path
        self.index: Optional[SimilarityIndex] = None
        self.embedding_matrix: Optional[np.ndarray] = None
        self.id_to_index: Dict[str, int] = {}
        self._built = False
        
    def build_index(self, embeddings: List[Any], 
                   style_encoder: Any = None,
                   pattern_encoder: Any = None,
                   region_data: Dict[str, Dict[str, Any]] = None):
        """
        Build the similarity index from embeddings.
        
        Args:
            embeddings: List of MapEmbedding objects
            style_encoder: Optional StyleEncoder for style-based search
            pattern_encoder: Optional PatternEncoder for pattern-based search
            region_data: Optional dictionary of raw region data
        """
        embeddings_dict = {}
        styles_dict = {}
        patterns_dict = {}
        metadata_dict = {}
        
        for emb in embeddings:
            region_id = emb.region_id
            embeddings_dict[region_id] = emb.vector
            
            # Get style
            if hasattr(emb, 'style') and emb.style:
                styles_dict[region_id] = emb.style
                
            # Get metadata
            metadata_dict[region_id] = {
                "region_type": emb.region_type,
                "dimensions": emb.dimensions,
                "embedding_id": emb.embedding_id
            }
            
        # Extract patterns if pattern encoder provided
        if pattern_encoder and region_data:
            for region_id, data in region_data.items():
                pattern = pattern_encoder.extract_pattern(data)
                patterns_dict[region_id] = pattern
                
        # Build embedding matrix
        region_ids = list(embeddings_dict.keys())
        vectors = [embeddings_dict[rid] for rid in region_ids]
        self.embedding_matrix = np.array(vectors)
        self.id_to_index = {rid: i for i, rid in enumerate(region_ids)}
        
        # Create index
        self.index = SimilarityIndex(
            index_id="similarity_index_v1",
            embeddings=embeddings_dict,
            styles=styles_dict,
            patterns=patterns_dict,
            metadata=metadata_dict,
            region_data=region_data or {}
        )
        
        self._built = True
        
    def _cosine_similarity(self, vector1: List[float], 
                          vector2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))
    
    def _euclidean_distance(self, vector1: List[float], 
                           vector2: List[float]) -> float:
        """Compute euclidean distance between two vectors."""
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        return float(np.linalg.norm(v1 - v2))
    
    def _style_similarity(self, style1: str, style2: str) -> float:
        """Compute similarity between two styles."""
        if style1 == style2:
            return 1.0
            
        # Define style relationships
        style_groups = {
            "dark": ["roshamuul", "soulwar", "library"],
            "bright": ["issavi", "falcon", "thais"],
            "exotic": ["cobra", "yalahar", "issavi"]
        }
        
        for group, styles in style_groups.items():
            if style1 in styles and style2 in styles:
                return 0.7
                
        return 0.3
    
    def _pattern_similarity(self, pattern1: Dict[str, float], 
                           pattern2: Dict[str, float]) -> float:
        """Compute similarity between two pattern profiles."""
        if not pattern1 or not pattern2:
            return 0.5
            
        # Compare key pattern features
        features = ["grid_score", "symmetry_score", "tile_density", 
                   "complexity_score", "avg_degree"]
        
        similarities = []
        for feature in features:
            val1 = pattern1.get(feature, 0)
            val2 = pattern2.get(feature, 0)
            diff = abs(val1 - val2)
            similarities.append(max(0, 1.0 - diff))
            
        return np.mean(similarities) if similarities else 0.5
    
    def find_similar(self, query_id: str, top_k: int = 10,
                    mode: str = "hybrid", 
                    style_weight: float = 0.3,
                    pattern_weight: float = 0.3,
                    embedding_weight: float = 0.4,
                    min_similarity: float = 0.0) -> List[SimilarityResult]:
        """
        Find regions similar to the query region.
        
        Args:
            query_id: ID of the query region
            top_k: Number of results to return
            mode: Similarity mode (embedding, style, pattern, hybrid)
            style_weight: Weight for style similarity in hybrid mode
            pattern_weight: Weight for pattern similarity in hybrid mode
            embedding_weight: Weight for embedding similarity in hybrid mode
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of SimilarityResult objects
        """
        if not self._built or not self.index:
            return []
            
        if query_id not in self.index.embeddings:
            return []
            
        query_vector = self.index.embeddings[query_id]
        query_style = self.index.styles.get(query_id, "unknown")
        query_pattern = self.index.patterns.get(query_id, {})
        
        results = []
        
        for region_id, target_vector in self.index.embeddings.items():
            if region_id == query_id:
                continue
                
            # Calculate similarities based on mode
            if mode == self.MODE_EMBEDDING:
                similarity = self._cosine_similarity(query_vector, target_vector)
            elif mode == self.MODE_STYLE:
                target_style = self.index.styles.get(region_id, "unknown")
                similarity = self._style_similarity(query_style, target_style)
            elif mode == self.MODE_PATTERN:
                target_pattern = self.index.patterns.get(region_id, {})
                similarity = self._pattern_similarity(query_pattern, target_pattern)
            else:  # Hybrid mode
                # Embedding similarity
                emb_sim = self._cosine_similarity(query_vector, target_vector)
                
                # Style similarity
                target_style = self.index.styles.get(region_id, "unknown")
                style_sim = self._style_similarity(query_style, target_style)
                
                # Pattern similarity
                target_pattern = self.index.patterns.get(region_id, {})
                pattern_sim = self._pattern_similarity(query_pattern, target_pattern)
                
                # Weighted combination
                similarity = (embedding_weight * emb_sim + 
                            style_weight * style_sim + 
                            pattern_weight * pattern_sim)
                
            if similarity >= min_similarity:
                # Determine match type
                if mode == self.MODE_HYBRID:
                    match_type = "hybrid"
                else:
                    match_type = mode
                    
                result = SimilarityResult(
                    query_id=query_id,
                    matched_id=region_id,
                    similarity_score=similarity,
                    match_type=match_type,
                    matched_region=self.index.region_data.get(region_id),
                    metadata={
                        "style": self.index.styles.get(region_id, "unknown"),
                        "region_type": self.index.metadata.get(region_id, {}).get("region_type", "unknown")
                    }
                )
                results.append(result)
                
        # Sort by similarity and return top k
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]
    
    def find_similar_by_style(self, style: str, top_k: int = 10,
                             min_similarity: float = 0.5) -> List[SimilarityResult]:
        """
        Find all regions matching a specific style.
        
        Args:
            style: Style name to search for
            top_k: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of SimilarityResult objects
        """
        if not self._built or not self.index:
            return []
            
        results = []
        
        for region_id, region_style in self.index.styles.items():
            if region_style == style:
                result = SimilarityResult(
                    query_id=f"style:{style}",
                    matched_id=region_id,
                    similarity_score=1.0,
                    match_type="style_exact",
                    matched_region=self.index.region_data.get(region_id),
                    metadata={
                        "style": region_style,
                        "region_type": self.index.metadata.get(region_id, {}).get("region_type", "unknown")
                    }
                )
                results.append(result)
                
        return results[:top_k]
    
    def find_similar_by_type(self, region_type: str, top_k: int = 10,
                            min_similarity: float = 0.5) -> List[SimilarityResult]:
        """
        Find all regions of a specific type.
        
        Args:
            region_type: Region type to search for
            top_k: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of SimilarityResult objects
        """
        if not self._built or not self.index:
            return []
            
        results = []
        
        for region_id, metadata in self.index.metadata.items():
            if metadata.get("region_type") == region_type:
                result = SimilarityResult(
                    query_id=f"type:{region_type}",
                    matched_id=region_id,
                    similarity_score=1.0,
                    match_type="type_exact",
                    matched_region=self.index.region_data.get(region_id),
                    metadata=metadata
                )
                results.append(result)
                
        return results[:top_k]
    
    def find_similar_to_vector(self, vector: List[float], top_k: int = 10,
                              min_similarity: float = 0.0) -> List[SimilarityResult]:
        """
        Find regions most similar to a given vector.
        
        Args:
            vector: Query vector
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of SimilarityResult objects
        """
        if not self._built or not self.index:
            return []
            
        results = []
        
        for region_id, target_vector in self.index.embeddings.items():
            similarity = self._cosine_similarity(vector, target_vector)
            
            if similarity >= min_similarity:
                result = SimilarityResult(
                    query_id="vector_query",
                    matched_id=region_id,
                    similarity_score=similarity,
                    match_type="vector",
                    matched_region=self.index.region_data.get(region_id),
                    metadata={
                        "style": self.index.styles.get(region_id, "unknown"),
                        "region_type": self.index.metadata.get(region_id, {}).get("region_type", "unknown")
                    }
                )
                results.append(result)
                
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]
    
    def find_clusters(self, k: int = 5, min_size: int = 3) -> Dict[str, List[str]]:
        """
        Find clusters of similar regions.
        
        Args:
            k: Number of clusters to find
            min_size: Minimum cluster size
            
        Returns:
            Dictionary mapping cluster IDs to lists of region IDs
        """
        if not self._built or not self.index:
            return {}
            
        # Simple k-means style clustering
        region_ids = list(self.index.embeddings.keys())
        vectors = [self.index.embeddings[rid] for rid in region_ids]
        vectors_array = np.array(vectors)
        
        if len(vectors_array) < k:
            k = len(vectors_array)
            
        # Initialize centroids randomly
        np.random.seed(42)
        centroid_indices = np.random.choice(len(vectors_array), k, replace=False)
        centroids = vectors_array[centroid_indices]
        
        # Iterate until convergence
        for _ in range(20):
            # Assign points to nearest centroid
            clusters = defaultdict(list)
            for i, vector in enumerate(vectors_array):
                distances = [np.linalg.norm(vector - centroid) for centroid in centroids]
                nearest = np.argmin(distances)
                clusters[nearest].append(region_ids[i])
                
            # Update centroids
            new_centroids = []
            for i in range(k):
                if clusters[i]:
                    cluster_vectors = vectors_array[[region_ids.index(rid) for rid in clusters[i]]]
                    new_centroids.append(np.mean(cluster_vectors, axis=0))
                else:
                    new_centroids.append(centroids[i])
                    
            centroids = np.array(new_centroids)
            
        # Filter by minimum size
        result = {}
        for cluster_id, members in clusters.items():
            if len(members) >= min_size:
                result[f"cluster_{cluster_id}"] = members
                
        return result
    
    def get_style_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics about styles in the index."""
        if not self._built or not self.index:
            return {}
            
        style_counts = defaultdict(int)
        style_types = defaultdict(lambda: defaultdict(int))
        
        for region_id, style in self.index.styles.items():
            style_counts[style] += 1
            region_type = self.index.metadata.get(region_id, {}).get("region_type", "unknown")
            style_types[style][region_type] += 1
            
        return {
            "style_counts": dict(style_counts),
            "style_type_distribution": {k: dict(v) for k, v in style_types.items()}
        }
    
    def get_type_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics about region types in the index."""
        if not self._built or not self.index:
            return {}
            
        type_counts = defaultdict(int)
        type_styles = defaultdict(lambda: defaultdict(int))
        
        for region_id, metadata in self.index.metadata.items():
            region_type = metadata.get("region_type", "unknown")
            type_counts[region_type] += 1
            style = self.index.styles.get(region_id, "unknown")
            type_styles[region_type][style] += 1
            
        return {
            "type_counts": dict(type_counts),
            "type_style_distribution": {k: dict(v) for k, v in type_styles.items()}
        }
    
    def save_index(self, output_path: str = None):
        """Save the similarity index to file."""
        if not self.index:
            return
            
        output_path = output_path or self.index_path
        if not output_path:
            return
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        data = {
            "version": "1.0",
            "index": {
                "index_id": self.index.index_id,
                "embeddings": self.index.embeddings,
                "styles": self.index.styles,
                "patterns": self.index.patterns,
                "metadata": self.index.metadata,
                "region_data": self.index.region_data
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_index(self, input_path: str = None):
        """Load the similarity index from file."""
        input_path = input_path or self.index_path
        if not input_path:
            return False
            
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
                
            index_data = data.get("index", {})
            self.index = SimilarityIndex(
                index_id=index_data.get("index_id", ""),
                embeddings=index_data.get("embeddings", {}),
                styles=index_data.get("styles", {}),
                patterns=index_data.get("patterns", {}),
                metadata=index_data.get("metadata", {}),
                region_data=index_data.get("region_data", {})
            )
            
            # Rebuild embedding matrix
            region_ids = list(self.index.embeddings.keys())
            vectors = [self.index.embeddings[rid] for rid in region_ids]
            self.embedding_matrix = np.array(vectors)
            self.id_to_index = {rid: i for i, rid in enumerate(region_ids)}
            
            self._built = True
            return True
            
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
            
    def query(self, query_string: str, top_k: int = 10) -> List[SimilarityResult]:
        """
        Process a natural language query.
        
        Supports queries like:
        - "Find maps similar to Roshamuul"
        - "Find dungeons like Issavi"
        - "Show me boss rooms"
        
        Args:
            query_string: Natural language query
            top_k: Number of results to return
            
        Returns:
            List of SimilarityResult objects
        """
        query_lower = query_string.lower()
        
        # Parse query intent
        if "similar to" in query_lower or "like" in query_lower:
            # Extract style/region name
            for style in ["roshamuul", "issavi", "soulwar", "library", 
                         "falcon", "cobra", "yalahar", "thais"]:
                if style in query_lower:
                    return self.find_similar_by_style(style, top_k)
                    
        if "dungeon" in query_lower:
            return self.find_similar_by_type("dungeon", top_k)
            
        if "boss" in query_lower:
            return self.find_similar_by_type("boss_room", top_k)
            
        if "temple" in query_lower:
            return self.find_similar_by_type("temple", top_k)
            
        if "city" in query_lower:
            return self.find_similar_by_type("city", top_k)
            
        # Default: try hybrid search
        return []
    
    def get_recommendations(self, region_id: str, 
                          count: int = 5) -> List[Dict[str, Any]]:
        """
        Get recommendations for a region.
        
        Args:
            region_id: ID of the region to get recommendations for
            count: Number of recommendations
            
        Returns:
            List of recommendation dictionaries
        """
        similar = self.find_similar(region_id, top_k=count, mode="hybrid")
        
        recommendations = []
        for result in similar:
            recommendations.append({
                "region_id": result.matched_id,
                "similarity": result.similarity_score,
                "style": result.metadata.get("style", "unknown"),
                "type": result.metadata.get("region_type", "unknown"),
                "reason": f"Similar {result.match_type} match"
            })
            
        return recommendations