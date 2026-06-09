"""
core/recovery.py

Crash recovery for Agente RME v1.0.0 GA.

Features:
  - Checkpointing: save a snapshot of the pipeline/world mid-run
  - Pipeline resume: pick up from the last successful checkpoint
  - Safe exports: write outputs to a temp file, then atomically rename
  - Rollback: revert to a previous OTBM/Lua/JSON artifact

Exports:
  - recovery_report.json

Usage:
    from core.recovery import RecoveryManager, Checkpoint
    rm = RecoveryManager()
    ck = rm.checkpoint(world, stage="export", metadata={"tiles": 4200})
    rm.export(ck, "output/checkpoint.json")
    # On failure:
    rm.rollback("output/generated.otbm")
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.observability.logger import _utc_iso


@dataclass
class Checkpoint:
    id: str
    stage: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload_path: str = ""
    success: bool = True
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RecoveryManager:
    """Manages checkpoints, atomic exports, and rollback."""

    def __init__(self, checkpoint_dir: str = ".checkpoint",
                 backups_dir: str = ".backups",
                 max_checkpoints: int = 5) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.backups_dir = Path(backups_dir)
        self.max_checkpoints = max_checkpoints
        self._checkpoints: List[Checkpoint] = []
        self._lock = threading.Lock()
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self._load_index()

    # ------------------------------------------------------------------
    # Checkpointing
    # ------------------------------------------------------------------

    def checkpoint(self, world: Any = None, stage: str = "unknown",
                   metadata: Optional[Dict[str, Any]] = None) -> Checkpoint:
        """Create a checkpoint. If world supports to_dict, payload is saved to disk."""
        meta = dict(metadata or {})
        ts = _utc_iso()
        ck_id = f"ck_{int(time.time() * 1000)}_{stage}"
        payload_path = ""
        if world is not None and hasattr(world, "to_dict"):
            payload_path = str(self.checkpoint_dir / f"{ck_id}.json")
            try:
                with open(payload_path, "w", encoding="utf-8") as f:
                    json.dump(world.to_dict(), f, indent=2, default=str, ensure_ascii=False)
            except OSError as e:
                payload_path = ""
                meta["payload_error"] = str(e)
        ck = Checkpoint(
            id=ck_id,
            stage=stage,
            timestamp=ts,
            metadata=meta,
            payload_path=payload_path,
        )
        with self._lock:
            self._checkpoints.append(ck)
            self._trim()
            self._save_index()
        return ck

    def _trim(self) -> None:
        while len(self._checkpoints) > self.max_checkpoints:
            old = self._checkpoints.pop(0)
            if old.payload_path:
                try:
                    os.remove(old.payload_path)
                except OSError:
                    pass

    def _index_path(self) -> Path:
        return self.checkpoint_dir / "index.json"

    def _save_index(self) -> None:
        with open(self._index_path(), "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self._checkpoints], f, indent=2, ensure_ascii=False)

    def _load_index(self) -> None:
        p = self._index_path()
        if not p.exists():
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._checkpoints = [Checkpoint(**c) for c in data if isinstance(c, dict)]
        except (OSError, json.JSONDecodeError, TypeError):
            self._checkpoints = []

    def checkpoints(self) -> List[Checkpoint]:
        return list(self._checkpoints)

    def last_successful(self, stage: Optional[str] = None) -> Optional[Checkpoint]:
        for ck in reversed(self._checkpoints):
            if not ck.success:
                continue
            if stage and ck.stage != stage:
                continue
            return ck
        return None

    def resume(self, stage: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load the last successful checkpoint payload (if any)."""
        ck = self.last_successful(stage)
        if ck is None or not ck.payload_path:
            return None
        p = Path(ck.payload_path)
        if not p.exists():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    # ------------------------------------------------------------------
    # Safe exports
    # ------------------------------------------------------------------

    def safe_write_bytes(self, data: bytes, target_path: str) -> str:
        """Atomically write bytes to target_path. Backs up any existing file."""
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            self._backup(target)
        # Write to temp in same directory, then rename
        fd, tmp_name = tempfile.mkstemp(prefix=".tmp_", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass
            os.replace(tmp_name, target)
        except Exception:
            try:
                os.remove(tmp_name)
            except OSError:
                pass
            raise
        return str(target)

    def safe_write_text(self, text: str, target_path: str) -> str:
        return self.safe_write_bytes(text.encode("utf-8"), target_path)

    def _backup(self, target: Path) -> Optional[Path]:
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self.backups_dir / f"{target.name}.{ts}.bak"
        try:
            shutil.copy2(target, backup_path)
            return backup_path
        except OSError:
            return None

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def rollback(self, target_path: str) -> Optional[str]:
        """Restore the most recent backup of target_path, if any."""
        target = Path(target_path)
        name = target.name
        candidates = sorted(
            self.backups_dir.glob(f"{name}.*.bak"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for c in candidates:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(c, target)
                return str(c)
            except OSError:
                continue
        return None

    def list_backups(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for p in self.backups_dir.glob("*.bak"):
            try:
                stat = p.stat()
            except OSError:
                continue
            out.append({
                "path": str(p),
                "name": p.name,
                "size_bytes": stat.st_size,
                "mtime": stat.st_mtime,
            })
        out.sort(key=lambda d: d["mtime"], reverse=True)
        return out

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def report(self) -> Dict[str, Any]:
        return {
            "timestamp": _utc_iso(),
            "checkpoint_dir": str(self.checkpoint_dir),
            "backups_dir": str(self.backups_dir),
            "max_checkpoints": self.max_checkpoints,
            "checkpoints_total": len(self._checkpoints),
            "checkpoints_successful": sum(1 for c in self._checkpoints if c.success),
            "checkpoints_failed": sum(1 for c in self._checkpoints if not c.success),
            "backups_total": sum(1 for _ in self.backups_dir.glob("*.bak")),
            "last_checkpoint": self._checkpoints[-1].to_dict() if self._checkpoints else None,
        }

    def export_report(self, path: str = "recovery_report.json") -> str:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(self.report(), f, indent=2, ensure_ascii=False)
        return str(out)
