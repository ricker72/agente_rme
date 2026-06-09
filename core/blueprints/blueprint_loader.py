from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .blueprint import Blueprint


class BlueprintLoadError(Exception):
    """Raised when a blueprint cannot be loaded from a file."""
    pass


class BlueprintLoader:
    """
    Loads Blueprint objects from JSON files on disk.

    Scans a directory tree for .json files, parses them,
    and returns Blueprint instances. Handles both the new
    tile-based format and the legacy descriptive format.

    Usage:
        loader = BlueprintLoader()
        count = loader.load_directory("data/blueprints/")
        bp = loader.get("issavi_temple_small")
    """

    def __init__(self):
        self._blueprints: Dict[str, Blueprint] = {}
        self._source_paths: Dict[str, Path] = {}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_file(self, path: str | Path) -> Optional[Blueprint]:
        """
        Load a single blueprint from a JSON file.

        Args:
            path: Path to the .json file.

        Returns:
            Blueprint instance, or None if loading/parsing fails.
        """
        p = Path(path)
        if not p.exists() or p.suffix.lower() != ".json":
            return None

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise BlueprintLoadError(f"Failed to parse {p}: {e}") from e

        if not isinstance(data, dict):
            raise BlueprintLoadError(f"Invalid blueprint format in {p}: expected dict, got {type(data).__name__}")

        bp = Blueprint.from_dict(data)
        self._blueprints[bp.name] = bp
        self._source_paths[bp.name] = p
        return bp

    def load_directory(self, directory: str | Path, recursive: bool = True) -> int:
        """
        Load all .json blueprint files from a directory.

        Args:
            directory: Root directory to scan.
            recursive: If True, scan subdirectories recursively.

        Returns:
            Number of blueprints successfully loaded.
        """
        base = Path(directory)
        if not base.exists() or not base.is_dir():
            return 0

        pattern = "**/*.json" if recursive else "*.json"
        count = 0
        errors: List[str] = []

        for f in sorted(base.glob(pattern)):
            try:
                bp = self.load_file(f)
                if bp is not None:
                    count += 1
            except BlueprintLoadError as e:
                errors.append(str(e))
                # Continue loading other files

        if errors:
            import logging
            for err in errors:
                logging.warning(err)

        return count

    def load_from_dict(self, data: Dict) -> Blueprint:
        """
        Load a blueprint from an in-memory dictionary.

        Args:
            data: Dictionary with blueprint specification.

        Returns:
            Blueprint instance.
        """
        bp = Blueprint.from_dict(data)
        self._blueprints[bp.name] = bp
        return bp

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    def get(self, name: str) -> Optional[Blueprint]:
        """Get a loaded blueprint by name."""
        return self._blueprints.get(name)

    def list_all(self) -> List[Blueprint]:
        """Return all loaded blueprints."""
        return list(self._blueprints.values())

    def list_names(self) -> List[str]:
        """Return sorted names of all loaded blueprints."""
        return sorted(self._blueprints.keys())

    def count(self) -> int:
        """Return the number of loaded blueprints."""
        return len(self._blueprints)

    def get_path(self, name: str) -> Optional[Path]:
        """Get the source file path for a blueprint by name."""
        return self._source_paths.get(name)

    def clear(self) -> None:
        """Clear all loaded blueprints."""
        self._blueprints.clear()
        self._source_paths.clear()

    # ------------------------------------------------------------------
    # Reload
    # ------------------------------------------------------------------

    def reload(self, name: str) -> Optional[Blueprint]:
        """Reload a single blueprint from its source file."""
        path = self._source_paths.get(name)
        if path is None or not path.exists():
            return None
        # Remove existing entry before reloading
        self._blueprints.pop(name, None)
        self._source_paths.pop(name, None)
        return self.load_file(path)

    def reload_all(self) -> int:
        """Reload all blueprints from their source files."""
        paths = dict(self._source_paths)
        self.clear()
        count = 0
        for name, path in paths.items():
            try:
                bp = self.load_file(path)
                if bp is not None:
                    count += 1
            except BlueprintLoadError:
                pass
        return count