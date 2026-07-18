"""Loader for official OpenTibia appearance data presence and fingerprint."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


class AppearanceLoader:
    def __init__(self, path: str | Path) -> None:
        self.catalog_path = Path(path)
        if self.catalog_path.name != "catalog-content.json":
            self.catalog_path = self.catalog_path.parent / "catalog-content.json"
        self.path = self._resolve_appearances_path()

    def load(self) -> dict[str, object]:
        if not self.path.exists():
            raise FileNotFoundError(f"missing file: {self.path}")
        data = self.path.read_bytes()
        if len(data) < 16:
            raise ValueError(f"invalid format: {self.path}")
        sha256 = hashlib.sha256(data).hexdigest()
        expected_hash = self._hash_from_name(self.path.name)
        if expected_hash and sha256 != expected_hash:
            raise ValueError(f"catalog hash mismatch for {self.path}: {sha256}")
        catalog = self._catalog_data()
        sprite_entries = [entry for entry in catalog if entry.get("type") == "sprite"]
        present_sprite_files = [
            entry
            for entry in sprite_entries
            if (self.catalog_path.parent / str(entry.get("file", ""))).exists()
        ]
        return {
            "source": str(self.path),
            "catalog": str(self.catalog_path),
            "bytes": len(data),
            "sha256": sha256,
            "format": "appearances.dat",
            "catalog_status": "HASHED_APPEARANCES_RESOLVED",
            "catalog_entry_count": len(catalog),
            "sprite_bundle_count": len(sprite_entries),
            "sprite_file_count": len(present_sprite_files),
            "sprite_files_missing": len(sprite_entries) - len(present_sprite_files),
        }

    def _resolve_appearances_path(self) -> Path:
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"missing file: {self.catalog_path}")
        for entry in self._catalog_data():
            if isinstance(entry, dict) and entry.get("type") == "appearances":
                file_name = str(entry.get("file", ""))
                path = self.catalog_path.parent / file_name
                if not path.exists():
                    raise FileNotFoundError(f"missing file: {path}")
                return path
        raise ValueError(f"appearances entry not found in {self.catalog_path}")

    def _hash_from_name(self, name: str) -> str:
        match = re.match(r"appearances-([0-9a-f]{64})\.dat$", name)
        return match.group(1) if match else ""

    def _catalog_data(self) -> list[dict[str, object]]:
        data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"invalid format: {self.catalog_path}")
        return [entry for entry in data if isinstance(entry, dict)]
