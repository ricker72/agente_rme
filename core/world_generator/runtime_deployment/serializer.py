from __future__ import annotations

import hashlib
import json
from typing import Any


def deterministic_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def fingerprint_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint_json(data: Any) -> str:
    return fingerprint_bytes(deterministic_json(data).encode("utf-8"))
