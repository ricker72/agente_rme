from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

FORBIDDEN = ("dofile", "loadfile", "os.", "io.", "require(", "Game.", "addEvent", "onUse", "onThink")


def validate_lua_runtime(root: Path) -> Dict[str, Any]:
    errors = []
    files = {}
    for name in ("world_metadata.lua", "navigation_metadata.lua"):
        path = root / name
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        forbidden = [token for token in FORBIDDEN if token in text]
        valid = path.exists() and bool(re.search(r"^\s*return\s+\{", text, re.M)) and text.count("{") == text.count("}") and not forbidden
        if not valid:
            errors.append(f"{name} invalid")
        files[name] = {"exists": path.exists(), "valid": valid, "forbidden_tokens": forbidden, "bytes": len(text.encode("utf-8"))}
    return {"artifact": "LUA_RUNTIME_VALIDATION", "valid": not errors, "files": files, "errors": errors}
