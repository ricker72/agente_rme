from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .blueprint import Blueprint
from .blueprint_loader import BlueprintLoader
from .blueprint_validator import BlueprintValidator, ValidationResult


class BlueprintRegistry:
    """
    Central registry for reusable blueprints.

    Combines loading, validation, and querying into one API.

    Usage:
        registry = BlueprintRegistry()
        registry.load_all("data/blueprints/")

        temple = registry.get("issavi_temple_small")
        all_bps = registry.list()
        issavi_bps = registry.by_theme("issavi")
        temple_count = registry.by_category("temple")
    """

    def __init__(self, asset_registry: Any = None):
        self._loader = BlueprintLoader()
        self._validator = BlueprintValidator(asset_registry)
        self._asset_registry = asset_registry

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_all(self, directory: str | Path) -> int:
        """
        Load all blueprints from a directory tree.

        Args:
            directory: Root directory to scan for .json blueprint files.

        Returns:
            Number of blueprints loaded.
        """
        return self._loader.load_directory(directory, recursive=True)

    def load_file(self, path: str | Path) -> Optional[Blueprint]:
        """
        Load a single blueprint from a JSON file.

        Args:
            path: Path to the .json file.

        Returns:
            Blueprint instance, or None on failure.
        """
        return self._loader.load_file(path)

    def register(self, blueprint: Blueprint) -> None:
        """
        Register a blueprint programmatically.

        Args:
            blueprint: Blueprint instance to register.
        """
        self._loader.load_from_dict(blueprint.to_dict())

    # ------------------------------------------------------------------
    # Query API — the main interface
    # ------------------------------------------------------------------

    def get(self, name: str) -> Optional[Blueprint]:
        """
        Get a blueprint by name.

        Args:
            name: The exact name of the blueprint (e.g., "issavi_temple_small").

        Returns:
            Blueprint instance, or None if not found.
        """
        return self._loader.get(name)

    def list(self) -> List[Blueprint]:
        """
        List all registered blueprints.

        Returns:
            List of all Blueprint instances.
        """
        return self._loader.list_all()

    def by_theme(self, theme: str) -> List[Blueprint]:
        """
        Get all blueprints matching a given theme.

        Args:
            theme: Theme name (e.g., "issavi", "roshamuul", "generic").

        Returns:
            List of Blueprint instances with matching theme.
        """
        theme_lower = theme.lower()
        return [bp for bp in self._loader.list_all() if bp.theme.lower() == theme_lower]

    def by_category(self, category: str) -> List[Blueprint]:
        """
        Get all blueprints of a given category.

        Args:
            category: Category name (e.g., "temple", "market", "bridge").

        Returns:
            List of Blueprint instances with matching category.
        """
        cat_lower = category.lower()
        return [
            bp for bp in self._loader.list_all() if bp.category.lower() == cat_lower
        ]

    def search(self, keyword: str) -> List[Blueprint]:
        """
        Search blueprints by keyword in name, theme, category, description,
        or tags.

        Args:
            keyword: Search term (case-insensitive).

        Returns:
            List of matching Blueprint instances.
        """
        kw = keyword.lower()
        results: List[Blueprint] = []
        for bp in self._loader.list_all():
            if (
                kw in bp.name.lower()
                or kw in bp.theme.lower()
                or kw in bp.category.lower()
                or kw in bp.description.lower()
                or any(kw in tag.lower() for tag in bp.tags)
            ):
                results.append(bp)
        return results

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def names(self) -> List[str]:
        """Return sorted list of all registered blueprint names."""
        return self._loader.list_names()

    def count(self) -> int:
        """Return total number of registered blueprints."""
        return self._loader.count()

    def summary(self) -> Dict[str, int]:
        """Return a summary dict: theme -> count, category -> count."""
        themes: Dict[str, int] = {}
        categories: Dict[str, int] = {}
        for bp in self._loader.list_all():
            themes[bp.theme] = themes.get(bp.theme, 0) + 1
            categories[bp.category] = categories.get(bp.category, 0) + 1
        return {
            "total": self._loader.count(),
            "by_theme": themes,
            "by_category": categories,
        }

    def clear(self) -> None:
        """Clear all registered blueprints."""
        self._loader.clear()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, name: str) -> Optional[ValidationResult]:
        """
        Validate a specific blueprint by name.

        Args:
            name: Blueprint name.

        Returns:
            ValidationResult, or None if blueprint not found.
        """
        bp = self._loader.get(name)
        if bp is None:
            return None
        return self._validator.validate(bp)

    def validate_all(self) -> Dict[str, ValidationResult]:
        """Validate all registered blueprints."""
        return self._validator.validate_batch(self._loader.list_all())

    # ------------------------------------------------------------------
    # Reload
    # ------------------------------------------------------------------

    def reload(self, name: str) -> Optional[Blueprint]:
        """Reload a single blueprint from its source file."""
        return self._loader.reload(name)

    def reload_all(self) -> int:
        """Reload all blueprints from their source files."""
        return self._loader.reload_all()
