"""
WG-20U Dataset Loader - Loads WG-20TE authoritative datasets.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import json


_DEFAULT_WORKSPACE = Path(__file__).resolve().parent.parent.parent


class Wg20uDatasetLoader:
    """Loads WG-20TE datasets for WG-20U consumption."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or _DEFAULT_WORKSPACE

    def load_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Load a single WG-20TE dataset by name."""
        path = self.workspace_root / dataset_name
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_name}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_all(self, dataset_names: list[str]) -> Dict[str, Dict[str, Any]]:
        """Load multiple WG-20TE datasets."""
        results = {}
        for name in dataset_names:
            try:
                results[name] = self.load_dataset(name)
            except FileNotFoundError:
                results[name] = {"error": f"Missing: {name}"}
        return results

    def load_optional_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Load an optional dataset, returning an empty mapping when absent."""
        path = self.workspace_root / dataset_name
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_live_trace(self) -> Dict[str, Any]:
        """Load authoritative RULE-41 live trace JSONL events."""
        path = self.workspace_root / "LIVE_GENERATION_TRACE.jsonl"
        events = []
        if not path.exists():
            return {"events": events, "missing": True}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                events.append(json.loads(line))
        return {"events": events, "missing": False}

    def load_rule41_trace_artifacts(self) -> Dict[str, Any]:
        """Load RULE-41 authoritative observability artifacts for WG-20U."""
        return {
            "LIVE_GENERATION_TRACE.jsonl": self.load_live_trace(),
            "EVENT_STREAM.json": self.load_optional_dataset("EVENT_STREAM.json"),
            "TRACE_REGISTRY.json": self.load_optional_dataset("TRACE_REGISTRY.json"),
            "GENERATION_TIMELINE.json": self.load_optional_dataset(
                "GENERATION_TIMELINE.json"
            ),
            "OBSERVABILITY_AUDIT.json": self.load_optional_dataset(
                "OBSERVABILITY_AUDIT.json"
            ),
        }

    def get_floor_graph(self) -> Dict[str, Any]:
        """Get floor graph data."""
        return self.load_dataset("WG20TE_FLOOR_GRAPH.json")

    def get_stair_connectivity(self) -> Dict[str, Any]:
        """Get stair connectivity data."""
        return self.load_dataset("WG20TE_STAIR_CONNECTIVITY.json")

    def get_ramp_connectivity(self) -> Dict[str, Any]:
        """Get ramp connectivity data."""
        return self.load_dataset("WG20TE_RAMP_CONNECTIVITY.json")

    def get_semantic_brush_resolution(self) -> Dict[str, Any]:
        """Get semantic brush resolution audit data."""
        return self.load_dataset("WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json")

    def get_role_uniqueness(self) -> Dict[str, Any]:
        """Get role uniqueness audit data."""
        return self.load_dataset("WG20TE_ROLE_UNIQUENESS_AUDIT.json")

    def get_building_access(self) -> Dict[str, Any]:
        """Get building access validation data."""
        return self.load_dataset("WG20TE_BUILDING_ACCESS_VALIDATION.json")

    def get_hunt_reachability(self) -> Dict[str, Any]:
        """Get hunt reachability data."""
        return self.load_dataset("WG20TE_HUNT_REACHABILITY.json")

    def get_path_continuity(self) -> Dict[str, Any]:
        """Get path continuity data."""
        return self.load_dataset("WG20TE_PATH_CONTINUITY.json")

    def get_validation(self) -> Dict[str, Any]:
        """Get WG-20TE validation data."""
        return self.load_dataset("WG20TE_VALIDATION.json")

    def get_quality_report(self) -> Dict[str, Any]:
        """Get quality report data."""
        return self.load_dataset("WG20TE_QUALITY_REPORT.json")
