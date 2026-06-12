"""
Tests for the BlueprintLoader class.
Covers file loading, directory scanning, errors, and reload.
"""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from core.blueprints import BlueprintLoader, Blueprint, BlueprintLoadError


class TestBlueprintLoader:
    """Test the BlueprintLoader file I/O operations."""

    @pytest.fixture
    def loader(self):
        """Create a fresh BlueprintLoader."""
        return BlueprintLoader()

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory with blueprint JSON files."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # Valid blueprint
            valid_bp = {
                "name": "test_blueprint",
                "theme": "test",
                "category": "building",
                "size": [10, 10],
                "tiles": [{"x": 0, "y": 0, "ground": 100}],
            }
            (tmp_path / "valid.json").write_text(json.dumps(valid_bp), encoding="utf-8")

            # Another valid blueprint in a subdir
            (tmp_path / "subdir").mkdir()
            another_bp = {
                "name": "nested_blueprint",
                "theme": "test",
                "category": "bridge",
                "size": [5, 20],
                "tiles": [{"x": 0, "y": 0, "ground": 200}],
            }
            (tmp_path / "subdir" / "nested.json").write_text(
                json.dumps(another_bp), encoding="utf-8"
            )

            # Invalid JSON file
            (tmp_path / "invalid.json").write_text("{bad json", encoding="utf-8")

            # Empty file
            (tmp_path / "empty.json").write_text("", encoding="utf-8")

            # Non-JSON file (should be ignored)
            (tmp_path / "notes.txt").write_text("not a blueprint", encoding="utf-8")

            yield tmp_path

    def test_load_file_valid(self, loader, temp_dir):
        """Load a valid blueprint JSON file."""
        bp = loader.load_file(temp_dir / "valid.json")
        assert bp is not None
        assert isinstance(bp, Blueprint)
        assert bp.name == "test_blueprint"
        assert bp.theme == "test"
        assert bp.width == 10
        assert bp.height == 10

    def test_load_file_nonexistent(self, loader):
        """Loading a non-existent file returns None."""
        bp = loader.load_file(Path("nonexistent_file_.json"))
        assert bp is None

    def test_load_directory_all(self, loader, temp_dir):
        """Load all valid blueprints from directory (recursive)."""
        count = loader.load_directory(temp_dir, recursive=True)
        assert count == 2  # valid.json + nested.json (invalid/empty are skipped)
        names = loader.list_names()
        assert "test_blueprint" in names
        assert "nested_blueprint" in names

    def test_load_directory_non_recursive(self, loader, temp_dir):
        """Load only top-level blueprints (non-recursive)."""
        count = loader.load_directory(temp_dir, recursive=False)
        assert count == 1  # Only valid.json
        names = loader.list_names()
        assert "test_blueprint" in names
        assert "nested_blueprint" not in names

    def test_load_directory_nonexistent(self, loader):
        """Loading a non-existent directory returns 0."""
        count = loader.load_directory(Path("/nonexistent/path/xyz"))
        assert count == 0

    def test_load_from_dict(self, loader):
        """Load a blueprint from an in-memory dict."""
        data = {
            "name": "dict_bp",
            "theme": "custom",
            "category": "test",
            "size": [8, 8],
            "tiles": [{"x": 0, "y": 0, "ground": 500}],
        }
        bp = loader.load_from_dict(data)
        assert bp.name == "dict_bp"
        assert bp.theme == "custom"

        # Should be accessible via get()
        assert loader.get("dict_bp") is bp

    def test_get_and_list(self, loader, temp_dir):
        """Test get(), list_all(), list_names(), count()."""
        loader.load_directory(temp_dir)
        assert loader.count() == 2

        bp = loader.get("test_blueprint")
        assert bp is not None

        assert loader.get("nonexistent") is None

        all_bps = loader.list_all()
        assert len(all_bps) == 2

        names = loader.list_names()
        assert names == sorted(names)

    def test_get_path(self, loader, temp_dir):
        """get_path() returns the source file path."""
        loader.load_file(temp_dir / "valid.json")
        path = loader.get_path("test_blueprint")
        assert path is not None
        assert path.name == "valid.json"

    def test_get_path_not_found(self, loader):
        """get_path() returns None for unknown blueprint."""
        assert loader.get_path("unknown") is None

    def test_reload(self, loader, temp_dir):
        """reload() reloads a blueprint from its source file."""
        loader.load_file(temp_dir / "valid.json")
        bp = loader.reload("test_blueprint")
        assert bp is not None
        assert bp.name == "test_blueprint"

    def test_reload_unknown(self, loader):
        """reload() returns None for unknown blueprint."""
        assert loader.reload("unknown") is None

    def test_reload_all(self, loader, temp_dir):
        """reload_all() reloads all blueprints."""
        loader.load_directory(temp_dir)
        count = loader.reload_all()
        assert count == 2

    def test_clear(self, loader, temp_dir):
        """clear() removes all loaded blueprints."""
        loader.load_directory(temp_dir)
        assert loader.count() == 2
        loader.clear()
        assert loader.count() == 0
        assert loader.list_all() == []

    def test_invalid_json_file(self, loader, temp_dir):
        """Loading an invalid JSON file raises BlueprintLoadError."""
        with pytest.raises(BlueprintLoadError):
            loader.load_file(temp_dir / "invalid.json")
