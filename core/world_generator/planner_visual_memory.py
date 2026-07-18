from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from core.safe_io import atomic_write_json, read_json_bounded
from core.world_generator.visual_map_composer import VisualCompositionReferenceAnalyzer


class PlannerVisualMemoryCache:
    """Persistent, deduplicated visual-prior memory for Mapper Planner."""

    FORMAT = "rme-planner-visual-memory-v2"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def ingest(
        self,
        references: Iterable[tuple[str | Path, tuple[str, ...]]],
    ) -> dict[str, Any]:
        cache = self.load()
        entries = {entry["sha256"]: entry for entry in cache.get("entries", ())}
        analyzer = VisualCompositionReferenceAnalyzer()
        added = updated = 0
        for source, tags in references:
            path = Path(source)
            digest = _sha256(path)
            metrics = asdict(analyzer.analyze_one(path))
            entry = {
                "sha256": digest,
                "source_name": path.name,
                "tags": sorted(set(str(tag) for tag in tags)),
                "metrics": metrics,
                "source_kind": "user_reference",
                "confidence": 1.0,
                "policy": "abstract visual metrics only; no pixels, coordinates or source geometry cached",
            }
            if digest in entries:
                updated += int(entries[digest] != entry)
            else:
                added += 1
            entries[digest] = entry
        cache = {
            "format": self.FORMAT,
            "entries": sorted(entries.values(), key=lambda value: value["sha256"]),
            "learned_priors": _learned_priors(entries.values()),
            "last_ingest": {"added": added, "updated": updated, "deduplicated_total": len(entries)},
        }
        atomic_write_json(self.path, cache)
        return cache

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"format": self.FORMAT, "entries": [], "learned_priors": {}}
        payload = read_json_bounded(
            self.path,
            default={"format": self.FORMAT, "entries": [], "learned_priors": {}},
        )
        if payload.get("format") == "rme-planner-visual-memory-v1":
            payload = self._migrate_v1(payload)
        if payload.get("format") != self.FORMAT:
            raise ValueError(f"Unsupported visual memory format: {payload.get('format')}")
        return payload

    def _migrate_v1(self, payload: dict[str, Any]) -> dict[str, Any]:
        entries = []
        for entry in payload.get("entries", ()):
            migrated = dict(entry)
            is_world = str(entry.get("source_name", "")).startswith("world.otbm:")
            migrated.setdefault("source_kind", "world_ephemeral" if is_world else "user_reference")
            migrated.setdefault("confidence", 0.8 if is_world else 1.0)
            entries.append(migrated)
        return {
            "format": self.FORMAT,
            "entries": entries,
            "learned_priors": _learned_priors(entries),
            "last_ingest": dict(payload.get("last_ingest", {})),
            "migration": "v1_to_v2_preserved_entries",
        }

    def ingest_abstract(
        self,
        observations: Iterable[dict[str, Any]],
        *,
        replace_source_kind: str | None = None,
    ) -> dict[str, Any]:
        cache = self.load()
        entries = {
            entry["sha256"]: entry
            for entry in cache.get("entries", ())
            if replace_source_kind is None or entry.get("source_kind") != replace_source_kind
        }
        added = updated = 0
        for observation in observations:
            metrics = dict(observation["metrics"])
            metrics["source_name"] = "anonymous-world-zone"
            tags = sorted(set(str(tag) for tag in observation.get("tags", ())))
            digest = str(observation.get("sha256") or _abstract_digest(metrics, tags))
            entry = {
                "sha256": digest,
                "source_name": "world.otbm:anonymous-zone",
                "tags": tags,
                "metrics": metrics,
                "source_kind": str(observation.get("source_kind", "world_ephemeral")),
                "confidence": max(0.1, min(1.0, float(observation.get("confidence", 0.8)))),
                "policy": "in-memory render discarded; abstract metrics only; no coordinates or tile stacks",
            }
            if digest in entries:
                updated += int(entries[digest] != entry)
            else:
                added += 1
            entries[digest] = entry
        cache = {
            "format": self.FORMAT,
            "entries": sorted(entries.values(), key=lambda value: value["sha256"]),
            "learned_priors": _learned_priors(entries.values()),
            "last_ingest": {"added": added, "updated": updated, "deduplicated_total": len(entries)},
        }
        atomic_write_json(self.path, cache)
        return cache


def _learned_priors(entries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(entries)
    if not rows:
        return {}
    metric_keys = ("entropy", "edge_density", "water_ratio", "nature_ratio", "dark_ratio")
    tag_counts: dict[str, int] = {}
    cooccurrence: Counter[str] = Counter()
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        source_kind = str(row.get("source_kind", "unknown"))
        source_group = "world_ephemeral" if source_kind.startswith("world_") else source_kind
        by_source[source_group].append(row)
        for tag in row["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            by_tag[tag].append(row)
        tags = sorted(set(row["tags"]))
        cooccurrence.update(
            f"{left}|{right}"
            for index, left in enumerate(tags)
            for right in tags[index + 1 :]
        )
    source_profiles = {
        source: _weighted_metrics(source_rows, metric_keys)
        for source, source_rows in sorted(by_source.items())
    }
    aggregate = {
        key: round(sum(profile[key] for profile in source_profiles.values()) / len(source_profiles), 6)
        for key in metric_keys
    }
    tag_profiles = {
        tag: {"reference_count": len(tag_rows), **_weighted_metrics(tag_rows, metric_keys)}
        for tag, tag_rows in sorted(by_tag.items())
    }
    return {
        "reference_count": len(rows),
        "aggregate": aggregate,
        "semantic_evidence": dict(sorted(tag_counts.items())),
        "semantic_cooccurrence": dict(cooccurrence.most_common(40)),
        "source_balanced_profiles": source_profiles,
        "profiles_by_tag": tag_profiles,
        "architectural_edge_target": aggregate["edge_density"],
        "water_envelope_target": aggregate["water_ratio"],
        "nature_cluster_bias": min(0.75, max(0.2, aggregate["nature_ratio"] * 5.0)),
        "dark_hunt_contrast_target": aggregate["dark_ratio"],
        "requires_multifloor": tag_counts.get("multifloor", 0) > 0,
        "requires_roofs": tag_counts.get("roof", 0) > 0,
        "requires_wall_continuity": tag_counts.get("wall_alignment", 0) > 0,
    }


def _weighted_metrics(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, float]:
    total_weight = sum(float(row.get("confidence", 1.0)) for row in rows) or 1.0
    return {
        key: round(
            sum(
                float(row["metrics"][key]) * float(row.get("confidence", 1.0))
                for row in rows
            )
            / total_weight,
            6,
        )
        for key in keys
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _abstract_digest(metrics: dict[str, Any], tags: list[str]) -> str:
    payload = json.dumps({"metrics": metrics, "tags": tags}, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
