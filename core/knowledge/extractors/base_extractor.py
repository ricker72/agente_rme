"""
BaseExtractor — shared helpers for all knowledge extractors.

The extractors accept any of:

  - `path`: file path (.otbm, .json, .lua)
  - `world`: a `WorldModel` instance
  - `data`: a dict that already represents a world or blueprint

The extractor normalises these into a `WorldDict` (plain python dict with
`tiles`, `regions`, `structures`, `spawns`, `cities`, `waypoints`, `meta`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

WorldDict = Dict[str, Any]


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (set, tuple)):
        return list(value)
    return [value]


def _coerce_world(obj: Any, source_label: str) -> WorldDict:
    """Normalize input to a dict with the standard world shape."""
    if obj is None:
        return {
            "tiles": [],
            "regions": [],
            "structures": [],
            "spawns": [],
            "cities": [],
            "waypoints": [],
            "meta": {"source": source_label},
        }
    if isinstance(obj, dict):
        # Already shaped?  Make sure all keys are present.
        out: WorldDict = {
            "tiles": list(obj.get("tiles", []) or []),
            "regions": list(obj.get("regions", []) or []),
            "structures": list(obj.get("structures", []) or []),
            "spawns": list(obj.get("spawns", []) or []),
            "cities": list(obj.get("cities", []) or obj.get("towns", []) or []),
            "waypoints": list(obj.get("waypoints", []) or []),
            "monsters": list(obj.get("monsters", []) or []),
            "items": list(obj.get("items", []) or []),
            "meta": dict(obj.get("meta", {}) or {}),
        }
        out["meta"].setdefault("source", source_label)
        # If the dict is a WorldModel.to_dict() shape it has the same keys.
        # If it is a blueprint shape, propagate patterns/structures.
        for k in (
            "name",
            "theme",
            "category",
            "patterns",
            "size",
            "entry",
            "description",
            "metadata",
            "width",
            "height",
        ):
            if k in obj and k not in out["meta"]:
                out["meta"][k] = obj[k]
        return out
    # WorldModel instance?
    if hasattr(obj, "to_dict"):
        try:
            d = obj.to_dict()
            return _coerce_world(d, source_label)
        except Exception:
            pass
    # Anything else — wrap it
    return {
        "meta": {"source": source_label, "raw": str(obj)},
        "tiles": [],
        "regions": [],
        "structures": [],
        "spawns": [],
        "cities": [],
        "waypoints": [],
    }


def _coerce_source(source: Union[str, Path, None]) -> str:
    if source is None:
        return "unknown"
    p = Path(source)
    return p.name or str(source)


class BaseExtractor:
    """
    Common scaffolding for knowledge extractors.

    Subclasses override `extract(world, source) -> List[KnowledgeEntry]`.
    """

    #: Subclass identifier used in metrics / catalog.
    NAME: str = "base"

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.NAME

    # ------------------------------------------------------------------
    # Source loading
    # ------------------------------------------------------------------

    def load(self, source: Union[str, Path, Dict[str, Any], Any]) -> WorldDict:
        """
        Load a world from any supported source.

        Accepts:
          - str/Path to a .json or .otbm file
          - dict (already a world)
          - WorldModel-like object
        """
        if isinstance(source, (str, Path)):
            p = Path(source)
            label = _coerce_source(p)
            if not p.exists():
                return _coerce_world(None, label)
            if p.suffix.lower() == ".json":
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    return _coerce_world(None, label)
                if isinstance(data, dict):
                    data.setdefault("meta", {})
                    if isinstance(data["meta"], dict):
                        data["meta"].setdefault("source", label)
                    return _coerce_world(data, label)
                return _coerce_world(None, label)
            # Non-JSON sources: try the OTBM importer, else fallback to empty.
            otbm_dict = self._try_otbm(p)
            if otbm_dict is not None:
                return _coerce_world(otbm_dict, label)
            return _coerce_world(None, label)
        if isinstance(source, dict):
            return _coerce_world(
                source,
                _coerce_source(
                    source.get("name") if isinstance(source, dict) else None
                ),
            )
        # Assume an object with .to_dict()
        return _coerce_world(source, _coerce_source(getattr(source, "name", None)))

    def _try_otbm(self, path: Path) -> Optional[Dict[str, Any]]:
        """Try to load an OTBM file via the project's OTBMImporter, if any."""
        try:
            from core.otbm.otbm_importer import OTBMImporter  # type: ignore
        except Exception:
            return None
        try:
            imp = OTBMImporter()
            res = imp.import_file(str(path))
            if isinstance(res, dict) and res.get("success"):
                return res.get("world_dict")
        except Exception:
            return None
        return None

    # ------------------------------------------------------------------
    # Default extract() — must be overridden
    # ------------------------------------------------------------------

    def extract(self, world: WorldDict, source: str = "") -> List[Any]:
        raise NotImplementedError

    def __call__(self, source: Union[str, Path, Dict[str, Any], Any]) -> List[Any]:
        """Convenience: load + extract in one call."""
        wd = self.load(source)
        label = (
            _coerce_source(source)
            if not isinstance(source, (dict,))
            else _as_str(wd.get("meta", {}).get("source"), "unknown")
        )
        return self.extract(wd, source=label)
