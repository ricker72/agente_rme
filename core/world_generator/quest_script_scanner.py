from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCANNER_VERSION = 1
DEFAULT_SERVER_ROOT = Path(
    r"C:\Users\samatha\OneDrive\Desktop\Servers\crystal_serve\crystal_serve"
)

_CONSTRUCTOR_RE = re.compile(
    r"\b(Action|MoveEvent|CreatureEvent|GlobalEvent|TalkAction|BossLever)\s*\("
)
_CALLBACK_RE = re.compile(r"\b(?:function\s+)?[A-Za-z_]\w*\.(on[A-Z]\w+)\s*(?:=\s*function|\()")
_REGISTER_RE = re.compile(r"\b[A-Za-z_]\w*:(aid|uid|id|type|position|register)\s*\(([^)]*)\)")
_STORAGE_RE = re.compile(
    r"\b(?:(?:player|Game|[A-Za-z_]\w*):?\.?)(getStorageValue|setStorageValue|addStorageValue)"
    r"\s*\(\s*([^,)]+)(?:,\s*([^)]*))?\)"
)
_SYMBOLIC_STORAGE_RE = re.compile(r"\b(?:Storage|GlobalStorage)(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
_DEPENDENCY_RE = re.compile(r"\b(?:require|dofile)\s*\(?\s*['\"]([^'\"]+)['\"]")
_API_RE = re.compile(r"\b([A-Za-z_]\w*)[:.]([A-Za-z_]\w*)\s*\(")
_POSITION_RE = re.compile(r"\bPosition\s*\(([^)]*)\)")
_ITEM_RE = re.compile(r"\b(addItem|removeItem|createItem|addItemEx)\s*\(\s*([^,)]+)(?:,\s*([^)]*))?")
_REWARD_RE = re.compile(
    r"\b(addExperience|addMoney|addBankBalance|addOutfit|addMount|addAchievement)"
    r"\s*\(\s*([^)]*)\)"
)
_MOVEMENT_RE = re.compile(r"\b(teleportTo|moveTo|doRelocate|transform|decay)\s*\(([^)]*)\)")
_MONSTER_RE = re.compile(r"\b(?:createMonster|createNpc|summonCreature)\s*\(\s*([^,)]+)")


class QuestScriptScanner:
    """Statically indexes Canary quest Lua without loading or executing Lua."""

    def __init__(
        self,
        root: str | Path = ".",
        server_root: str | Path = DEFAULT_SERVER_ROOT,
    ) -> None:
        self.root = Path(root).resolve()
        self.server_root = Path(server_root).resolve()
        self.scripts_root = self.server_root / "data-global" / "scripts"
        self.quest_root = self.scripts_root / "quests"
        self.cache_path = self.root / "exports" / "planner_knowledge" / "QUEST_SCRIPT_SCAN_REPORT.json"

    def scan_cached(self, *, force: bool = False) -> dict[str, Any]:
        manifest = self._manifest()
        if not force and self.cache_path.is_file():
            try:
                cached = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if cached.get("manifest_sha256") == manifest["sha256"]:
                    return cached
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
        report = self.scan(manifest)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
        temporary.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.cache_path)
        return report

    def scan(self, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
        manifest = manifest or self._manifest()
        files: list[dict[str, Any]] = []
        packages: dict[str, list[dict[str, Any]]] = defaultdict(list)
        totals: Counter[str] = Counter()
        for path in self._lua_files():
            raw = path.read_bytes()
            text = raw.decode("utf-8", errors="replace")
            relative = path.relative_to(self.scripts_root).as_posix()
            scope = "quest" if path.is_relative_to(self.quest_root) else "support"
            package = self._package(relative, scope)
            facts = self._facts(text)
            row = {
                "relative_path": relative,
                "scope": scope,
                "package": package,
                "language": "Lua",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                **facts,
            }
            files.append(row)
            packages[package].append(row)
            totals.update({
                "files": 1,
                scope: 1,
                "callbacks": len(facts["callbacks"]),
                "identifiers": len(facts["identifiers"]),
                "storage_transitions": len(facts["storage_transitions"]),
                "rewards": len(facts["rewards"]),
                "movements": len(facts["movements"]),
            })
        package_rows = [self._summarize_package(name, rows) for name, rows in sorted(packages.items())]
        return {
            "status": "PASS" if files else "BLOCKED",
            "scanner_version": SCANNER_VERSION,
            "manifest_sha256": manifest["sha256"],
            "source_root": str(self.scripts_root),
            "file_count": len(files),
            "quest_file_count": totals["quest"],
            "support_file_count": totals["support"],
            "package_count": len(package_rows),
            "totals": dict(totals),
            "files": files,
            "packages": package_rows,
            "policy": {
                "executes_lua": False,
                "static_analysis_only": True,
                "archives_access_scope": "analysis_only",
                "planner_receives_source": False,
                "planner_receives_normalized_patterns": True,
            },
        }

    def _manifest(self) -> dict[str, Any]:
        digest = hashlib.sha256()
        count = 0
        total_bytes = 0
        for path in self._lua_files():
            raw = path.read_bytes()
            relative = path.relative_to(self.scripts_root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(raw).digest())
            count += 1
            total_bytes += len(raw)
        return {"sha256": digest.hexdigest(), "file_count": count, "bytes": total_bytes}

    def _lua_files(self) -> list[Path]:
        if not self.scripts_root.is_dir():
            return []
        return sorted(self.scripts_root.rglob("*.lua"), key=lambda path: path.as_posix().lower())

    @staticmethod
    def _package(relative: str, scope: str) -> str:
        parts = Path(relative).parts
        if scope == "quest" and len(parts) > 1:
            return parts[1]
        return "/".join(parts[:2]) if len(parts) > 1 else parts[0]

    @staticmethod
    def _facts(source: str) -> dict[str, Any]:
        clean = _strip_lua_comments(source)
        constructors = sorted(set(_CONSTRUCTOR_RE.findall(clean)))
        callbacks = sorted(set(_CALLBACK_RE.findall(clean)))
        dependencies = sorted(set(_DEPENDENCY_RE.findall(clean)))
        api_calls = sorted({f"{owner}.{method}" for owner, method in _API_RE.findall(clean)})

        identifiers = []
        for kind, arguments in _REGISTER_RE.findall(clean):
            if kind == "register":
                continue
            for value in _split_arguments(arguments):
                identifiers.append({"kind": kind, "value": value})
        identifiers = _unique_dicts(identifiers, ("kind", "value"))

        transitions = []
        for operation, storage, value in _STORAGE_RE.findall(clean):
            transitions.append({
                "storage": storage.strip(),
                "operation": operation,
                "value": value.strip() if value else "",
            })
        known = {(row["storage"], row["operation"]) for row in transitions}
        for storage in _SYMBOLIC_STORAGE_RE.findall(clean):
            if not any(key[0] == storage for key in known):
                transitions.append({"storage": storage, "operation": "reference", "value": ""})
        transitions = _unique_dicts(transitions, ("storage", "operation", "value"))

        rewards = []
        for operation, item, amount in _ITEM_RE.findall(clean):
            rewards.append({
                "kind": "item" if operation in {"addItem", "addItemEx"} else "item_mutation",
                "operation": operation,
                "item": item.strip(),
                "amount": amount.strip() if amount else "1",
            })
        for operation, arguments in _REWARD_RE.findall(clean):
            rewards.append({"kind": operation, "operation": operation, "item": "", "amount": arguments.strip()})
        rewards = _unique_dicts(rewards, ("kind", "operation", "item", "amount"))

        movements = [
            {"kind": operation, "expression": arguments.strip()}
            for operation, arguments in _MOVEMENT_RE.findall(clean)
        ]
        movements.extend({"kind": "position", "expression": value.strip()} for value in _POSITION_RE.findall(clean))
        movements = _unique_dicts(movements, ("kind", "expression"))
        actors = sorted(set(value.strip() for value in _MONSTER_RE.findall(clean)))
        return {
            "constructors": constructors,
            "callbacks": callbacks,
            "dependencies": dependencies,
            "api_calls": api_calls,
            "identifiers": identifiers,
            "storage_transitions": transitions,
            "rewards": rewards,
            "movements": movements,
            "actors": actors,
            "metrics": {
                "lines": source.count("\n") + 1,
                "constructors": len(constructors),
                "callbacks": len(callbacks),
                "api_calls": len(api_calls),
            },
        }

    @staticmethod
    def _summarize_package(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        constructors = Counter(value for row in rows for value in row["constructors"])
        callbacks = Counter(value for row in rows for value in row["callbacks"])
        identifiers = Counter(value["kind"] for row in rows for value in row["identifiers"])
        reward_kinds = Counter(value["kind"] for row in rows for value in row["rewards"])
        movement_kinds = Counter(value["kind"] for row in rows for value in row["movements"])
        storage_refs = {value["storage"] for row in rows for value in row["storage_transitions"]}
        grammar = ["trigger", "preconditions"]
        if storage_refs:
            grammar.append("storage_transition")
        if movement_kinds:
            grammar.append("world_movement")
        if reward_kinds:
            grammar.append("reward")
        grammar.append("event_registration")
        return {
            "name": name,
            "scope": "quest" if all(row["scope"] == "quest" for row in rows) else "support",
            "script_count": len(rows),
            "language": "Lua",
            "constructors": dict(constructors),
            "callbacks": dict(callbacks),
            "identifier_kinds": dict(identifiers),
            "storage_count": len(storage_refs),
            "reward_kinds": dict(reward_kinds),
            "movement_kinds": dict(movement_kinds),
            "actors": sorted({actor for row in rows for actor in row["actors"]})[:32],
            "generation_grammar": grammar,
        }

    @staticmethod
    def compact_for_prompt(package: dict[str, Any]) -> dict[str, Any]:
        return {
            key: package[key]
            for key in (
                "name", "scope", "script_count", "language", "constructors", "callbacks",
                "identifier_kinds", "storage_count", "reward_kinds", "movement_kinds",
                "generation_grammar",
            )
        }


def _strip_lua_comments(source: str) -> str:
    source = re.sub(r"--\[\[.*?\]\]", "", source, flags=re.DOTALL)
    return re.sub(r"--[^\r\n]*", "", source)


def _split_arguments(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _unique_dicts(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for row in rows:
        marker = tuple(row[key] for key in keys)
        if marker not in seen:
            seen.add(marker)
            result.append(row)
    return result


__all__ = ["DEFAULT_SERVER_ROOT", "SCANNER_VERSION", "QuestScriptScanner"]
