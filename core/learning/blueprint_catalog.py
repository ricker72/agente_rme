"""
HITO 17 — Blueprint Catalog: Persistent storage and retrieval of learned blueprints.

Features:
- Automatic persistence to data/blueprints/
- Indexing by theme, category, tags
- Version control for blueprints
- Search and filtering
- Statistics and analytics
"""

from __future__ import annotations

import json
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from core.blueprints.blueprint import Blueprint
from core.blueprints.blueprint_registry import BlueprintRegistry


@dataclass
class BlueprintIndexEntry:
    """Index entry for fast lookup."""
    name: str
    theme: str
    category: str
    version: str
    tags: List[str]
    difficulty: str
    tile_count: int
    area: int
    source: str
    created_at: str
    updated_at: str
    file_path: str
    quality_score: float = 0.0
    usage_count: int = 0


class BlueprintCatalog:
    """
    Persistent catalog of learned blueprints.
    
    Provides:
    - Add/remove blueprints
    - Search by multiple criteria
    - Statistics and analytics
    - Version management
    - Automatic backup
    """
    
    def __init__(self, catalog_dir: str = "data/blueprints/"):
        """
        Initialize the catalog.
        
        Args:
            catalog_dir: Directory for blueprint storage
        """
        self.catalog_dir = Path(catalog_dir)
        self.catalog_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file
        self.index_path = self.catalog_dir / "_catalog_index.json"
        
        # Use existing registry for loading
        self.registry = BlueprintRegistry()
        
        # Local index for fast queries
        self._index: Dict[str, BlueprintIndexEntry] = {}
        self._loaded = False
        
        # Load existing index or build from files
        self._load_index()
    
    def _load_index(self):
        """Load or rebuild the catalog index."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r') as f:
                    data = json.load(f)
                
                for bp_name, entry_data in data.get("blueprints", {}).items():
                    self._index[bp_name] = BlueprintIndexEntry(**entry_data)
                
                self._loaded = True
                return
            except Exception:
                pass  # Fall through to rebuild
        
        # Rebuild from files
        self._rebuild_index()
    
    def _rebuild_index(self):
        """Rebuild index from blueprint files."""
        self._index.clear()
        
        for bp_file in self.catalog_dir.glob("*.json"):
            if bp_file.stem.startswith("_"):
                continue
            
            try:
                bp = self.registry.load_file(bp_file)
                if bp:
                    entry = self._create_index_entry(bp, str(bp_file))
                    self._index[bp.name] = entry
            except Exception:
                continue
        
        self._save_index()
        self._loaded = True
    
    def _create_index_entry(self, bp: Blueprint, file_path: str) -> BlueprintIndexEntry:
        """Create index entry from blueprint."""
        now = datetime.now().isoformat()
        
        # Check if file exists for created date
        created_at = now
        if os.path.exists(file_path):
            created_at = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
        
        return BlueprintIndexEntry(
            name=bp.name,
            theme=bp.theme,
            category=bp.category,
            version=bp.version,
            tags=bp.metadata.tags,
            difficulty=bp.metadata.difficulty,
            tile_count=len(bp.tiles),
            area=bp.area,
            source=bp.name.split("_")[0] if "_" in bp.name else bp.name,
            created_at=created_at,
            updated_at=now,
            file_path=file_path,
            quality_score=0.0,
            usage_count=0,
        )
    
    def _save_index(self):
        """Save index to disk."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "blueprints": {},
        }
        
        for bp_name, entry in self._index.items():
            data["blueprints"][bp_name] = asdict(entry)
        
        with open(self.index_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_blueprint(self, blueprint: Blueprint) -> BlueprintIndexEntry:
        """
        Add a blueprint to the catalog.
        
        Args:
            blueprint: Blueprint to add
            
        Returns:
            Index entry for the added blueprint
        """
        # Save blueprint to file
        bp_file = self.catalog_dir / f"{blueprint.name}.json"
        
        # Prepare data with extraction metadata
        bp_data = blueprint.to_dict()
        bp_data["_catalog"] = {
            "added_at": datetime.now().isoformat(),
            "tile_count": len(blueprint.tiles),
            "category": blueprint.category,
            "theme": blueprint.theme,
        }
        
        bp_file.write_text(
            json.dumps(bp_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        
        # Register in registry
        self.registry.register(blueprint)
        
        # Create and store index entry
        entry = self._create_index_entry(blueprint, str(bp_file))
        self._index[blueprint.name] = entry
        self._save_index()
        
        return entry
    
    def get_blueprint(self, name: str) -> Optional[Blueprint]:
        """Get a blueprint by name."""
        return self.registry.get(name)
    
    def remove_blueprint(self, name: str) -> bool:
        """
        Remove a blueprint from the catalog.
        
        Args:
            name: Blueprint name
            
        Returns:
            True if removed, False if not found
        """
        if name not in self._index:
            return False
        
        # Remove file
        bp_file = self.catalog_dir / f"{name}.json"
        if bp_file.exists():
            bp_file.unlink()
        
        # Remove from registry
        # Registry doesn't have remove, but we can clear and reload
        
        # Remove from index
        del self._index[name]
        self._save_index()
        
        return True
    
    def update_blueprint(self, blueprint: Blueprint) -> BlueprintIndexEntry:
        """Update an existing blueprint."""
        if blueprint.name not in self._index:
            return self.add_blueprint(blueprint)
        
        # Update file
        bp_file = self.catalog_dir / f"{blueprint.name}.json"
        bp_data = blueprint.to_dict()
        bp_data["_catalog"] = {
            "added_at": self._index[blueprint.name].created_at,
            "updated_at": datetime.now().isoformat(),
            "tile_count": len(blueprint.tiles),
            "category": blueprint.category,
            "theme": blueprint.theme,
        }
        
        bp_file.write_text(
            json.dumps(bp_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        
        # Update registry
        self.registry.register(blueprint)
        
        # Update index
        old_entry = self._index[blueprint.name]
        new_entry = BlueprintIndexEntry(
            name=blueprint.name,
            theme=blueprint.theme,
            category=blueprint.category,
            version=blueprint.version,
            tags=blueprint.metadata.tags,
            difficulty=blueprint.metadata.difficulty,
            tile_count=len(blueprint.tiles),
            area=blueprint.area,
            source=old_entry.source,
            created_at=old_entry.created_at,
            updated_at=datetime.now().isoformat(),
            file_path=str(bp_file),
            quality_score=old_entry.quality_score,
            usage_count=old_entry.usage_count,
        )
        self._index[blueprint.name] = new_entry
        self._save_index()
        
        return new_entry
    
    def list_all(self) -> List[Blueprint]:
        """List all blueprints in the catalog."""
        return self.registry.list_all()
    
    def list_names(self) -> List[str]:
        """List all blueprint names."""
        return sorted(self._index.keys())
    
    def count(self) -> int:
        """Return total number of blueprints."""
        return len(self._index)
    
    # Search & Filter
    def by_theme(self, theme: str) -> List[Blueprint]:
        """Get blueprints by theme."""
        theme_lower = theme.lower()
        names = [name for name, entry in self._index.items() 
                 if entry.theme.lower() == theme_lower]
        return [self.registry.get(name) for name in names if self.registry.get(name)]
    
    def by_category(self, category: str) -> List[Blueprint]:
        """Get blueprints by category."""
        cat_lower = category.lower()
        names = [name for name, entry in self._index.items() 
                 if entry.category.lower() == cat_lower]
        return [self.registry.get(name) for name in names if self.registry.get(name)]
    
    def by_tag(self, tag: str) -> List[Blueprint]:
        """Get blueprints containing a tag."""
        tag_lower = tag.lower()
        names = [name for name, entry in self._index.items() 
                 if any(tag_lower in t.lower() for t in entry.tags)]
        return [self.registry.get(name) for name in names if self.registry.get(name)]
    
    def by_difficulty(self, difficulty: str) -> List[Blueprint]:
        """Get blueprints by difficulty."""
        diff_lower = difficulty.lower()
        names = [name for name, entry in self._index.items() 
                 if entry.difficulty.lower() == diff_lower]
        return [self.registry.get(name) for name in names if self.registry.get(name)]
    
    def by_size_range(self, min_area: int = 0, max_area: int = 100000) -> List[Blueprint]:
        """Get blueprints within area range."""
        names = [name for name, entry in self._index.items() 
                 if min_area <= entry.area <= max_area]
        return [self.registry.get(name) for name in names if self.registry.get(name)]
    
    def by_tile_count_range(self, min_tiles: int = 0, max_tiles: int = 10000) -> List[Blueprint]:
        """Get blueprints within tile count range."""
        names = [name for name, entry in self._index.items() 
                 if min_tiles <= entry.tile_count <= max_tiles]
        return [self.registry.get(name) for name in names if self.registry.get(name)]
    
    def search(self, query: str) -> List[Blueprint]:
        """Search blueprints by name, theme, category, or tags."""
        query_lower = query.lower()
        results = []
        
        for name, entry in self._index.items():
            if (query_lower in name.lower() or
                query_lower in entry.theme.lower() or
                query_lower in entry.category.lower() or
                any(query_lower in tag.lower() for tag in entry.tags)):
                bp = self.registry.get(name)
                if bp:
                    results.append(bp)
        
        return results
    
    def get_by_quality(self, min_score: float = 0.0, max_score: float = 1.0) -> List[Blueprint]:
        """Get blueprints by quality score range."""
        names = [name for name, entry in self._index.items() 
                 if min_score <= entry.quality_score <= max_score]
        return [self.registry.get(name) for name in names if self.registry.get(name)]
    
    # Statistics
    def get_statistics(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        if not self._index:
            return {
                "total": 0,
                "by_theme": {},
                "by_category": {},
                "by_difficulty": {},
                "avg_tiles": 0,
                "avg_area": 0,
                "total_tiles": 0,
                "version_distribution": {},
            }
        
        themes = defaultdict(int)
        categories = defaultdict(int)
        difficulties = defaultdict(int)
        versions = defaultdict(int)
        total_tiles = 0
        total_area = 0
        
        for entry in self._index.values():
            themes[entry.theme] += 1
            categories[entry.category] += 1
            difficulties[entry.difficulty] += 1
            versions[entry.version] += 1
            total_tiles += entry.tile_count
            total_area += entry.area
        
        return {
            "total": len(self._index),
            "by_theme": dict(themes),
            "by_category": dict(categories),
            "by_difficulty": dict(difficulties),
            "avg_tiles": total_tiles / len(self._index),
            "avg_area": total_area / len(self._index),
            "total_tiles": total_tiles,
            "version_distribution": dict(versions),
            "largest_blueprint": max(self._index.values(), key=lambda e: e.area).name if self._index else None,
            "most_detailed": max(self._index.values(), key=lambda e: e.tile_count).name if self._index else None,
        }
    
    def get_theme_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed statistics per theme."""
        theme_stats = defaultdict(lambda: {
            "count": 0, "categories": defaultdict(int), 
            "avg_tiles": 0, "total_tiles": 0, "total_area": 0
        })
        
        for entry in self._index.values():
            stats = theme_stats[entry.theme]
            stats["count"] += 1
            stats["categories"][entry.category] += 1
            stats["total_tiles"] += entry.tile_count
            stats["total_area"] += entry.area
        
        result = {}
        for theme, stats in theme_stats.items():
            result[theme] = {
                "count": stats["count"],
                "categories": dict(stats["categories"]),
                "avg_tiles": stats["total_tiles"] / stats["count"],
                "avg_area": stats["total_area"] / stats["count"],
            }
        
        return result
    
    # Version Management
    def get_versions(self, name: str) -> List[Dict[str, Any]]:
        """Get version history (placeholder - would need version files)."""
        # This would require keeping version history
        # For now return current version info
        if name in self._index:
            entry = self._index[name]
            return [{
                "version": entry.version,
                "updated_at": entry.updated_at,
                "tile_count": entry.tile_count,
                "area": entry.area,
            }]
        return []
    
    def set_quality_score(self, name: str, score: float):
        """Update quality score for a blueprint."""
        if name in self._index:
            self._index[name].quality_score = max(0.0, min(1.0, score))
            self._save_index()
    
    def increment_usage(self, name: str):
        """Increment usage counter."""
        if name in self._index:
            self._index[name].usage_count += 1
            self._save_index()
    
    def get_most_used(self, count: int = 10) -> List[Blueprint]:
        """Get most used blueprints."""
        sorted_entries = sorted(self._index.values(), 
                               key=lambda e: e.usage_count, reverse=True)
        names = [e.name for e in sorted_entries[:count]]
        return [self.registry.get(n) for n in names if self.registry.get(n)]
    
    # Backup & Maintenance
    def backup(self, backup_dir: str) -> str:
        """Create a backup of the catalog."""
        backup_path = Path(backup_dir) / f"blueprint_catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all blueprint files
        for bp_file in self.catalog_dir.glob("*.json"):
            if not bp_file.stem.startswith("_"):
                shutil.copy2(bp_file, backup_path / bp_file.name)
        
        # Copy index
        if self.index_path.exists():
            shutil.copy2(self.index_path, backup_path / "_catalog_index.json")
        
        return str(backup_path)
    
    def restore_backup(self, backup_dir: str) -> bool:
        """Restore from a backup."""
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            return False
        
        # Clear current
        for bp_file in self.catalog_dir.glob("*.json"):
            bp_file.unlink()
        
        # Copy from backup
        for bp_file in backup_path.glob("*.json"):
            shutil.copy2(bp_file, self.catalog_dir / bp_file.name)
        
        # Reload
        self._rebuild_index()
        return True
    
    def cleanup_duplicates(self, similarity_threshold: float = 0.95) -> int:
        """Remove duplicate blueprints (placeholder)."""
        # This would require comparing blueprints
        # For now just return 0
        return 0
    
    def export_catalog_index(self, output_path: str):
        """Export catalog index for external use."""
        data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "blueprints": [],
        }
        
        for name, entry in self._index.items():
            bp = self.registry.get(name)
            if bp:
                data["blueprints"].append({
                    "name": name,
                    "theme": entry.theme,
                    "category": entry.category,
                    "version": entry.version,
                    "tags": entry.tags,
                    "difficulty": entry.difficulty,
                    "tile_count": entry.tile_count,
                    "area": entry.area,
                    "source": entry.source,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at,
                    "quality_score": entry.quality_score,
                    "usage_count": entry.usage_count,
                    "description": bp.description,
                    "is_tile_based": bp.is_tile_based,
                })
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)