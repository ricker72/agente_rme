# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Provenance Tracker.

Ensures Rule 4 compliance: every blueprint must know its origin.
Tracks the full lineage of blueprints through the extraction,
analysis, and generation pipeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models.blueprint_v2 import BlueprintV2, Provenance


class ProvenanceTracker:
    """
    Tracks provenance for all BlueprintV2 objects.

    Provides a complete audit trail of where each blueprint came from,
    what dataset it was extracted from, what version of the generator
    created it, and what seed was used.
    """

    def __init__(self) -> None:
        self._provenance_log: Dict[str, Provenance] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def track(self, bp: BlueprintV2) -> None:
        """
        Register a blueprint's provenance for tracking.

        Args:
            bp: BlueprintV2 with provenance data.
        """
        self._provenance_log[bp.blueprint_id] = bp.provenance

    def get_provenance(self, blueprint_id: str) -> Optional[Provenance]:
        """
        Get provenance for a specific blueprint.

        Args:
            blueprint_id: The blueprint's unique ID.

        Returns:
            Provenance or None.
        """
        return self._provenance_log.get(blueprint_id)

    def get_by_source(self, source: str) -> List[Provenance]:
        """
        Get all provenances from a specific source.

        Args:
            source: Source name (e.g. "Issavi", "Roshamuul").

        Returns:
            List of Provenance records.
        """
        return [p for p in self._provenance_log.values() if p.source == source]

    def get_by_dataset(self, dataset: str) -> List[Provenance]:
        """
        Get all provenances from a specific dataset.

        Args:
            dataset: Dataset name (e.g. "knowledge_dataset_v3").

        Returns:
            List of Provenance records.
        """
        return [p for p in self._provenance_log.values() if p.dataset == dataset]

    def create_provenance(
        self,
        source: str,
        dataset: str = "blueprint_intelligence",
        seed: int = 0,
        author: str = "blueprint_intelligence_v2",
    ) -> Provenance:
        """
        Create a new provenance record.

        Args:
            source: Source name.
            dataset: Dataset name.
            seed: Random seed.
            author: Author/creator identifier.

        Returns:
            New Provenance instance.
        """
        return Provenance(
            source=source,
            dataset=dataset,
            generator_version="2.0",
            seed=seed,
            extraction_timestamp=datetime.now().isoformat(),
            author=author,
        )

    def list_all(self) -> Dict[str, Provenance]:
        """List all tracked provenances."""
        return dict(self._provenance_log)

    def count(self) -> int:
        """Number of tracked blueprints."""
        return len(self._provenance_log)

    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of all tracked provenance.

        Returns:
            Dict with counts by source, dataset, and version.
        """
        sources: Dict[str, int] = {}
        datasets: Dict[str, int] = {}
        versions: Dict[str, int] = {}

        for p in self._provenance_log.values():
            sources[p.source] = sources.get(p.source, 0) + 1
            datasets[p.dataset] = datasets.get(p.dataset, 0) + 1
            versions[p.generator_version] = versions.get(p.generator_version, 0) + 1

        return {
            "total": len(self._provenance_log),
            "by_source": sources,
            "by_dataset": datasets,
            "by_version": versions,
        }

    # ------------------------------------------------------------------
    # Provenance verification
    # ------------------------------------------------------------------

    def verify(self, bp: BlueprintV2) -> bool:
        """
        Verify that a blueprint has valid provenance (Rule 4 compliance).

        Args:
            bp: BlueprintV2 to verify.

        Returns:
            True if provenance is complete and valid.
        """
        p = bp.provenance
        return bool(
            p.source
            and p.dataset
            and p.generator_version
            and p.extraction_timestamp
            and p.author
        )

    @staticmethod
    def get_lineage(bp: BlueprintV2) -> Dict[str, str]:
        """
        Get a human-readable lineage for a blueprint.

        Args:
            bp: BlueprintV2.

        Returns:
            Dict with lineage info.
        """
        p = bp.provenance
        return {
            "blueprint_id": bp.blueprint_id,
            "name": bp.name,
            "source": p.source,
            "dataset": p.dataset,
            "version": p.generator_version,
            "seed": str(p.seed),
            "extracted_at": p.extraction_timestamp,
            "author": p.author,
        }
