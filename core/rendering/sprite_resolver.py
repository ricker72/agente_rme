"""Resolve OpenTibia assets to official appearance sprite references."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .appearance_loader import AppearanceLoader
from .appearance_models import ResolvedSprite


class SpriteResolver:
    """Maps item/client IDs to appearance records without inventing sprite IDs."""

    def __init__(
        self,
        loader: AppearanceLoader | None = None,
        workspace_root: str | Path = ".",
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.loader = loader or AppearanceLoader(workspace_root=self.workspace_root).load()
        self.item_catalog: dict[str, dict[str, Any]] = self._load_json("APPEARANCE_ITEM_CATALOG.json")

    def resolve_asset(self, asset: object) -> ResolvedSprite:
        item_id = int(getattr(asset, "asset_id", 0) or 0)
        client_id = getattr(asset, "client_id", None)
        name = str(getattr(asset, "name", ""))
        category = str(getattr(asset, "category", ""))
        source = str(getattr(asset, "source_file", ""))
        return self.resolve(item_id, int(client_id) if client_id is not None else None, name, category, source)

    def resolve(
        self,
        item_id: int,
        client_id: int | None = None,
        name: str = "",
        category: str = "",
        source: str = "",
    ) -> ResolvedSprite:
        if self.loader.report is None:
            self.loader.load()
        if self.loader.report and self.loader.report.status == "UNSUPPORTED_FORMAT":
            return ResolvedSprite(item_id, client_id, None, status="UNSUPPORTED_FORMAT", reason=self.loader.report.error)

        candidates = self._candidate_appearance_ids(item_id, client_id)
        partial_candidate: int | None = None
        for candidate in candidates:
            record = self.loader.record(candidate)
            if record is None:
                continue
            partial_candidate = candidate
            if record.sprite_ids:
                return ResolvedSprite(
                    item_id=item_id,
                    client_id=client_id,
                    appearance_id=candidate,
                    sprite_ids=record.sprite_ids,
                    status="RESOLVED",
                    name=name,
                    category=category,
                    source=source,
                )
        if partial_candidate is not None:
            return ResolvedSprite(
                item_id=item_id,
                client_id=client_id,
                appearance_id=partial_candidate,
                status="PARTIAL",
                reason="appearance record has no sprite IDs",
                name=name,
                category=category,
                source=source,
            )
        return ResolvedSprite(
            item_id=item_id,
            client_id=client_id,
            appearance_id=None,
            status="UNRESOLVED",
            reason="no matching appearance record",
            name=name,
            category=category,
            source=source,
        )

    def _candidate_appearance_ids(self, item_id: int, client_id: int | None) -> list[int]:
        candidates: list[int] = []
        for value in (client_id, item_id):
            if value is not None and int(value) > 0:
                candidates.append(int(value))
        item = self.item_catalog.get(str(item_id), {})
        for brush in item.get("brushes", []) or []:
            lookid = brush.get("lookid")
            if lookid and str(lookid).isdigit():
                candidates.append(int(lookid))
        for key in ("client_id", "appearance_id", "lookid"):
            value = item.get(key)
            if value is not None and str(value).isdigit():
                candidates.append(int(value))
        return list(dict.fromkeys(candidates))

    def _load_json(self, name: str) -> dict[str, Any]:
        path = self.workspace_root / name
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
