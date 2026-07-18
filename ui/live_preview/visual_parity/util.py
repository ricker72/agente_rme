"""Utility functions for visual parity module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)