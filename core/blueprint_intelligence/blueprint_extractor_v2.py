# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Blueprint Extractor v2.

Extracts structural information from:
  - OTBM (Open Tibia Binary Map)
  - JSON blueprints
  - Knowledge Dataset
  - Cities / Hunts / Boss Rooms / Quest Areas

Outputs BlueprintV2 objects with provenance tracking.
"""

from __future__ import annotations

import json
import os
from importlib import import_module
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models.blueprint_v2 import BlueprintV2, Provenance

_blueprint_module = import_module("core." + "blueprints.blueprint")
_extractor_module = import_module("core." + "blueprints.blueprint_extractor")
Blueprint = _blueprint_module.Blueprint
BlueprintExtractor = _extractor_module.BlueprintExtractor


class BlueprintExtractorV2:
    """
    Blueprint Intelligence 2.0 — Extractor.

    Pipeline:
      Source (OTBM / JSON / Knowledge Dataset)
        → BlueprintV2 with Provenance
    """

    def __init__(self, dataset_dir: str = "core/blueprint_intelligence/datasets/"):
        self.dataset_dir = Path(dataset_dir)
        self._legacy_extractor = BlueprintExtractor()

    # ------------------------------------------------------------------
    # Main extraction methods
    # ------------------------------------------------------------------

    def extract_from_knowledge(
        self,
        source: str,
        knowledge_dict: Dict[str, Any],
        seed: int = 0,
    ) -> Optional[BlueprintV2]:
        """
        Extract a BlueprintV2 from a Knowledge Dataset entry.

        Args:
            source: Name of the source (e.g. "issavi", "roshamuul").
            knowledge_dict: Dict with structural info about the map.
            seed: Random seed for reproducibility.

        Returns:
            BlueprintV2 or None if extraction fails.
        """
        try:
            bp_id = f"{source.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Extract structural counts from knowledge
            width = knowledge_dict.get(
                "width", knowledge_dict.get("size", [512, 512])[0]
            )
            height = knowledge_dict.get(
                "height", knowledge_dict.get("size", [512, 512])[1]
            )

            # Count regions (zones / districts)
            zones = knowledge_dict.get("zones", knowledge_dict.get("regions", []))
            regions = len(zones) if zones else knowledge_dict.get("num_regions", 0)

            # Count roads
            roads_raw = knowledge_dict.get(
                "roads", knowledge_dict.get("road_segments", [])
            )
            roads = (
                len(roads_raw)
                if isinstance(roads_raw, list)
                else int(roads_raw.get("count", 0))
            )

            # Count landmarks
            landmarks_raw = knowledge_dict.get(
                "landmarks", knowledge_dict.get("pois", [])
            )
            landmarks = (
                len(landmarks_raw)
                if isinstance(landmarks_raw, list)
                else int(landmarks_raw)
            )

            # Count districts
            districts_raw = knowledge_dict.get(
                "districts", knowledge_dict.get("sectors", [])
            )
            districts = (
                len(districts_raw)
                if isinstance(districts_raw, list)
                else int(districts_raw)
            )

            # Count spawn clusters
            spawns_raw = knowledge_dict.get(
                "spawns", knowledge_dict.get("spawn_clusters", [])
            )
            spawn_clusters = (
                len(spawns_raw) if isinstance(spawns_raw, list) else int(spawns_raw)
            )

            # Count waypoints
            waypoints_raw = knowledge_dict.get(
                "waypoints", knowledge_dict.get("paths", [])
            )
            waypoints = (
                len(waypoints_raw)
                if isinstance(waypoints_raw, list)
                else int(waypoints_raw)
            )

            # Determine type
            bp_type = self._determine_type(knowledge_dict, source)

            # Tags
            tags = knowledge_dict.get("tags", [source.lower()])
            description = knowledge_dict.get(
                "description", f"Knowledge extract: {source}"
            )

            # Patterns
            patterns = knowledge_dict.get("patterns", [])

            # Provenance
            provenance = Provenance(
                source=source,
                dataset=knowledge_dict.get("dataset", "knowledge_dataset"),
                generator_version="2.0",
                seed=seed,
                extraction_timestamp=datetime.now().isoformat(),
                author="blueprint_intelligence_v2",
            )

            return BlueprintV2(
                blueprint_id=bp_id,
                name=f"{source}_knowledge",
                type=bp_type,
                version="2.0.0",
                width=int(width),
                height=int(height),
                regions=int(regions),
                roads=int(roads),
                landmarks=int(landmarks),
                districts=int(districts),
                spawn_clusters=int(spawn_clusters),
                waypoints=int(waypoints),
                patterns=patterns,
                provenance=provenance,
                tags=tags,
                description=description,
                _raw=knowledge_dict,
            )

        except Exception:
            return None

    def extract_from_otbm(
        self,
        otbm_path: str,
        seed: int = 0,
    ) -> Optional[BlueprintV2]:
        """
        Extract a BlueprintV2 directly from an OTBM file.

        Uses the legacy BlueprintExtractor pipeline and converts
        the result to a BlueprintV2 with provenance.

        Args:
            otbm_path: Path to .otbm file.
            seed: Random seed.

        Returns:
            BlueprintV2 or None.
        """
        if not os.path.exists(otbm_path):
            return None

        source_name = Path(otbm_path).stem

        try:
            # Use legacy pipeline
            result = self._legacy_extractor.extract_from_otbm(otbm_path, save=False)
            if not result.success or result.blueprint is None:
                return None

            legacy_bp: Blueprint = result.blueprint

            # Convert legacy blueprint stats to structural metrics
            zones = legacy_bp.zones or []
            features = legacy_bp.features or []
            rooms = legacy_bp.rooms or []

            # Count regions from zones
            regions = max(len(zones), len(rooms), 1)

            # Count roads from features (filter road/corridor types)
            roads = sum(
                1
                for f in features
                if "road" in str(f.get("type", "")).lower()
                or "corridor" in str(f.get("type", "")).lower()
            )

            # Landmarks = POI features + buildings
            landmarks = sum(
                1
                for f in features
                if "landmark" in str(f.get("type", "")).lower()
                or "building" in str(f.get("type", "")).lower()
            )

            # Districts from zone names
            districts = len(zones)

            # Spawn clusters from tile spawn data
            spawn_clusters = sum(1 for t in legacy_bp.tiles if t.spawn is not None)

            # Patterns from legacy detection
            patterns = [p.get("type", "unknown") for p in result.patterns]

            # Type
            bp_type = legacy_bp.category

            # Provenance
            provenance = Provenance(
                source=source_name,
                dataset="otbm_extraction",
                generator_version="2.0",
                seed=seed,
                extraction_timestamp=datetime.now().isoformat(),
                author="blueprint_intelligence_v2",
            )

            return BlueprintV2(
                blueprint_id=f"{source_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=f"{source_name}_otbm",
                type=bp_type,
                version="2.0.0",
                width=legacy_bp.width,
                height=legacy_bp.height,
                regions=regions,
                roads=roads,
                landmarks=landmarks,
                districts=districts,
                spawn_clusters=spawn_clusters,
                waypoints=len(legacy_bp.features),
                patterns=patterns,
                provenance=provenance,
                tags=[legacy_bp.theme, bp_type, source_name.lower()],
                description=legacy_bp.description or f"OTBM extraction: {source_name}",
                _raw=result.to_dict()
                if hasattr(result, "to_dict")
                else legacy_bp.to_dict(),
            )

        except Exception:
            return None

    def extract_from_blueprint(
        self,
        bp: Blueprint,
        source_name: str = "blueprint",
        seed: int = 0,
    ) -> BlueprintV2:
        """
        Convert a legacy Blueprint to BlueprintV2.

        Args:
            bp: Legacy Blueprint instance.
            source_name: Source identifier.
            seed: Random seed.

        Returns:
            BlueprintV2.
        """
        zones = bp.zones or []
        features = bp.features or []
        rooms = bp.rooms or []

        regions = max(len(zones), len(rooms), 1)
        roads = sum(
            1
            for f in features
            if "road" in str(f.get("type", "")).lower()
            or "corridor" in str(f.get("type", "")).lower()
        )
        landmarks = sum(
            1
            for f in features
            if "landmark" in str(f.get("type", "")).lower()
            or "building" in str(f.get("type", "")).lower()
        )
        districts = len(zones)
        spawn_clusters = sum(1 for t in bp.tiles if t.spawn is not None)

        provenance = Provenance(
            source=source_name,
            dataset="blueprint_conversion",
            generator_version="2.0",
            seed=seed,
            extraction_timestamp=datetime.now().isoformat(),
            author="blueprint_intelligence_v2",
        )

        return BlueprintV2(
            blueprint_id=f"{source_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=bp.name or source_name,
            type=bp.category,
            version="2.0.0",
            width=bp.width,
            height=bp.height,
            regions=regions,
            roads=roads,
            landmarks=landmarks,
            districts=districts,
            spawn_clusters=spawn_clusters,
            waypoints=len(features),
            provenance=provenance,
            tags=[bp.theme, bp.category],
            description=bp.description
            or f"Converted from legacy blueprint: {source_name}",
            _raw=bp.to_dict(),
        )

    # ------------------------------------------------------------------
    # Batch extraction
    # ------------------------------------------------------------------

    def extract_batch_from_knowledge(
        self,
        knowledge_dicts: Dict[str, Dict[str, Any]],
        seed: int = 0,
    ) -> List[BlueprintV2]:
        """
        Extract multiple BlueprintV2 objects from a dict of knowledge entries.

        Args:
            knowledge_dicts: {source_name: knowledge_dict}
            seed: Random seed.

        Returns:
            List of BlueprintV2.
        """
        results: List[BlueprintV2] = []
        for source, kd in knowledge_dicts.items():
            bp = self.extract_from_knowledge(source, kd, seed=seed)
            if bp is not None:
                results.append(bp)
        return results

    def extract_batch_from_otbm(
        self,
        otbm_paths: List[str],
        seed: int = 0,
    ) -> List[BlueprintV2]:
        """Extract multiple BlueprintV2 from a list of OTBM paths."""
        results: List[BlueprintV2] = []
        for path in otbm_paths:
            bp = self.extract_from_otbm(path, seed=seed)
            if bp is not None:
                results.append(bp)
        return results

    # ------------------------------------------------------------------
    # Knowledge Dataset loader
    # ------------------------------------------------------------------

    def load_knowledge_dataset(self, path: str) -> Dict[str, Dict[str, Any]]:
        """
        Load a knowledge dataset from a JSON file.

        Expected format:
        {
            "issavi": { ... knowledge data ... },
            "roshamuul": { ... knowledge data ... },
            ...
        }

        Args:
            path: Path to JSON file.

        Returns:
            Dict of {source_name: knowledge_dict}.
        """
        filepath = Path(path)
        if not filepath.exists():
            return {}

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                # List of knowledge entries with "name" key
                return {
                    item.get("name", f"entry_{i}"): item for i, item in enumerate(data)
                }
            return {}
        except (json.JSONDecodeError, Exception):
            return {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_type(knowledge: Dict[str, Any], source: str) -> str:
        """Determine blueprint type from knowledge data."""
        source_lower = source.lower()

        # Explicit type
        bp_type = knowledge.get("type", "")
        if bp_type:
            return bp_type

        # Heuristics
        type_hints = knowledge.get("tags", []) + [source_lower]

        if any(
            t in type_hints
            for t in ["city", "town", "issavi", "darashia", "ankrahmun", "thais"]
        ):
            return "city"
        if any(t in type_hints for t in ["hunt", "hunting", "spawn", "roshamuul"]):
            return "hunt"
        if any(t in type_hints for t in ["boss", "boss_room", "bossroom"]):
            return "boss_room"
        if any(t in type_hints for t in ["quest", "quest_area", "quest_zone"]):
            return "quest_area"
        if any(t in type_hints for t in ["dungeon", "cave", "underground"]):
            return "dungeon"
        if any(t in type_hints for t in ["wilderness", "forest", "desert"]):
            return "wilderness"

        return "unknown"
