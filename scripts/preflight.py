from __future__ import annotations

import runpy
from pathlib import Path


def _guardian_preflight() -> Path | None:
    home = Path.home()
    candidates = []
    codex_home = Path.home() / ".codex"
    candidates.append(codex_home / "skills" / "rme-opentibia-code-guardian" / "scripts" / "preflight.py")
    candidates.append(home / ".codex" / "skills" / "rme-opentibia-code-guardian" / "scripts" / "preflight.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


if __name__ == "__main__":
    script = _guardian_preflight()
    if script is None:
        raise SystemExit(
            "rme-opentibia-code-guardian preflight script was not found in the local Codex skills."
        )
    runpy.run_path(str(script), run_name="__main__")
