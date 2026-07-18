"""
CampaignPackage — mandatory wrapper that guarantees a campaign is *always*
present after the pipeline runs.

Hito 26.1C — Campaign Export Fix.

Design contract:
    * A ``CampaignPackage`` is NEVER ``None``.
    * If the full generator fails, ``CampaignPackage.minimal()`` returns a
      well-formed package (with the required keys: ``quests``, ``bosses``,
      ``raids``, ``story``, ``rewards``) so the export stage can always
      serialize to ``campaign.json``.
    * The status flag (``PackageStatus.OK``, ``FALLBACK``, ``EMPTY``) tells
      downstream consumers whether the package came from a real generation
      or a safety fallback.

This is the single source of truth consumed by:
    * QuestAgent      → builds the package
    * ExportAgent     → always writes ``campaign.json`` from it
    * Tests           → validate the contract
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class PackageStatus(str, Enum):
    """Lifecycle status of a CampaignPackage."""

    OK = "ok"  # Generated successfully
    FALLBACK = "fallback"  # Pipeline errored, fallback produced
    EMPTY = "empty"  # No data, minimal scaffold only


# Top-level required keys (validated by CampaignValidator).
REQUIRED_KEYS = ("quests", "bosses", "raids", "story", "rewards")


@dataclass
class CampaignPackage:
    """
    Mandatory, non-``None`` campaign container.

    The ``campaign`` field holds the real data (a ``Campaign`` object, a
    ``dict`` or another package); the convenience dict-properties expose
    the required keys (``quests``, ``bosses``, ``raids``, ``story``,
    ``rewards``) defaulting to safe empty values.
    """

    workflow_id: str = ""
    theme: str = "default"
    level_range: List[int] = field(default_factory=lambda: [1, 200])
    campaign: Optional[Any] = None
    status: PackageStatus = PackageStatus.OK
    errors: List[str] = field(default_factory=list)
    generated_at: str = ""
    source: str = "CampaignGenerator"

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()
        if isinstance(self.level_range, tuple):
            self.level_range = list(self.level_range)
        if isinstance(self.status, str):
            try:
                self.status = PackageStatus(self.status)
            except ValueError:
                self.status = PackageStatus.FALLBACK

    # ------------------------------------------------------------------
    # Factory: minimal / safe fallback
    # ------------------------------------------------------------------

    @classmethod
    def minimal(
        cls,
        theme: str = "default",
        level_range: Union[List[int], tuple] = (1, 200),
        workflow_id: str = "",
        errors: Optional[List[str]] = None,
    ) -> "CampaignPackage":
        """
        Build a well-formed empty campaign package.

        Used as a guaranteed-last-resort fallback so the export stage
        ALWAYS has something to serialize to ``campaign.json``.
        """
        return cls(
            workflow_id=workflow_id,
            theme=theme,
            level_range=list(level_range),
            campaign=None,
            status=PackageStatus.EMPTY,
            errors=list(errors or []),
            source="CampaignPackage.minimal",
        )

    @classmethod
    def from_campaign(
        cls,
        campaign: Any,
        workflow_id: str = "",
        theme: str = "default",
        level_range: Union[List[int], tuple] = (1, 200),
        errors: Optional[List[str]] = None,
    ) -> "CampaignPackage":
        """
        Wrap a real ``Campaign`` (or dict) into a package.

        ``errors`` defaults to empty; if non-empty, the status is promoted
        to ``FALLBACK``.
        """
        errs = list(errors or [])
        status = PackageStatus.FALLBACK if errs else PackageStatus.OK

        # Extract theme/level_range from the inner campaign if available.
        try:
            if hasattr(campaign, "theme") and campaign.theme:
                theme = campaign.theme
        except Exception:  # pragma: no cover — defensive
            pass
        try:
            if hasattr(campaign, "level_range") and campaign.level_range:
                lr = campaign.level_range
                level_range = list(lr) if isinstance(lr, (list, tuple)) else level_range
        except Exception:  # pragma: no cover — defensive
            pass

        return cls(
            workflow_id=workflow_id,
            theme=theme,
            level_range=list(level_range),
            campaign=campaign,
            status=status,
            errors=errs,
            source="CampaignGenerator",
        )

    # ------------------------------------------------------------------
    # Convenience accessors (always return valid data)
    # ------------------------------------------------------------------

    @property
    def quests(self) -> List[Dict[str, Any]]:
        """Always returns a list of quest dicts (possibly empty).

        Resolution order:
          1. Inner ``campaign.quests`` if present
          2. ``campaign.side_quests`` (alias used by CampaignGenerator)
          3. ``campaign.main_story.chapters`` (main story arcs as quests)
        """
        data = self._campaign_data()
        val = data.get("quests")
        if isinstance(val, list) and val:
            return val
        if isinstance(val, dict) and val:
            return [val]

        # Fallback: side_quests
        sq = data.get("side_quests", [])
        if isinstance(sq, list) and sq:
            return sq
        if isinstance(sq, dict) and sq:
            return [sq]

        # Fallback: main_story.chapters
        ms = data.get("main_story")
        if isinstance(ms, dict):
            chapters = ms.get("chapters")
            if isinstance(chapters, list) and chapters:
                return chapters

        return []

    @property
    def bosses(self) -> List[Dict[str, Any]]:
        data = self._campaign_data()
        val = data.get("bosses", [])
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            return [val]
        return []

    @property
    def raids(self) -> List[Dict[str, Any]]:
        data = self._campaign_data()
        val = data.get("raids", [])
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            return [val]
        return []

    @property
    def story(self) -> Dict[str, Any]:
        """Always returns a story dict (possibly empty)."""
        data = self._campaign_data()
        val = data.get("story", data.get("main_story", {}))
        if isinstance(val, dict):
            return val
        return {}

    @property
    def rewards(self) -> Dict[str, Any]:
        """Always returns a rewards dict (possibly empty)."""
        data = self._campaign_data()
        val = data.get("rewards", {})
        if isinstance(val, dict):
            return val
        return {}

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a fully JSON-serializable dict."""
        campaign_dict: Dict[str, Any] = self._campaign_data()
        # Build the top-level "quests" list by merging main story chapters
        # and side quests so the validator / consumers always see something.
        quests_list: List[Dict[str, Any]] = []
        # 1) explicit quests
        explicit = campaign_dict.get("quests")
        if isinstance(explicit, list):
            quests_list.extend(explicit)
        elif isinstance(explicit, dict) and explicit:
            quests_list.append(explicit)
        # 2) main_story.chapters (when not already in quests)
        ms = campaign_dict.get("main_story")
        if isinstance(ms, dict):
            chapters = ms.get("chapters")
            if isinstance(chapters, list):
                quests_list.extend(chapters)
        # 3) side_quests
        sq = campaign_dict.get("side_quests", [])
        if isinstance(sq, list):
            quests_list.extend(sq)
        elif isinstance(sq, dict) and sq:
            quests_list.append(sq)

        return {
            "workflow_id": self.workflow_id,
            "theme": self.theme,
            "level_range": list(self.level_range),
            "status": (
                self.status.value
                if isinstance(self.status, PackageStatus)
                else str(self.status)
            ),
            "source": self.source,
            "errors": list(self.errors),
            "generated_at": self.generated_at,
            # Required keys (explicit at top level for export)
            "quests": quests_list,
            "bosses": campaign_dict.get("bosses", []) or [],
            "raids": campaign_dict.get("raids", []) or [],
            "story": campaign_dict.get("story", campaign_dict.get("main_story", {}))
            or {},
            "rewards": campaign_dict.get("rewards", {}) or {},
            # Full inner campaign for consumers that want everything
            "campaign": campaign_dict,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def save(self, path: str) -> str:
        """Write the package to ``campaign.json``. Returns the path."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return path

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _campaign_data(self) -> Dict[str, Any]:
        """Coerce the inner ``campaign`` to a dict safely."""
        c = self.campaign
        if c is None:
            return {}
        if isinstance(c, dict):
            return c
        if hasattr(c, "to_dict"):
            try:
                d = c.to_dict()
                if isinstance(d, dict):
                    return d
            except Exception:  # pragma: no cover — defensive
                return {}
        # Last resort: asdict (dataclass)
        try:
            return asdict(c)  # type: ignore[arg-type]
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Sentinel: guarantee a non-None package
    # ------------------------------------------------------------------

    @staticmethod
    def ensure(value: Optional["CampaignPackage"], **kwargs: Any) -> "CampaignPackage":
        """
        Coerce ``None`` or any falsy value into a minimal valid package.

        This is the single guard every consumer (agents, tests, exports)
        should use to comply with the "never return None" contract.

        ``None``, empty strings, ``0``, ``False``, empty lists/dicts all
        become a ``PackageStatus.EMPTY`` minimal package. Non-empty
        ``dict`` values become ``PackageStatus.OK`` packages. Non-empty
        values of any other type are wrapped.
        """
        if isinstance(value, CampaignPackage):
            return value
        if value is None or value == "" or value == 0 or value is False:
            return CampaignPackage.minimal(**kwargs)
        if isinstance(value, (list, tuple, set)):
            if not value:
                return CampaignPackage.minimal(**kwargs)
            return CampaignPackage.from_campaign(value, **kwargs)
        if isinstance(value, dict):
            if not value:
                return CampaignPackage.minimal(**kwargs)
            return CampaignPackage.from_campaign(value, **kwargs)
        # Wrap unexpected types so we still satisfy the contract.
        return CampaignPackage.from_campaign(value, **kwargs)
