"""Core-backed knowledge adapter."""

from __future__ import annotations

import logging
import importlib
from pathlib import Path
from typing import Any, Callable

from ui.adapters._helpers import CORE_UNAVAILABLE, read_attr, safe_str
from ui.models.knowledge_dto import KnowledgeMetricsDTO, KnowledgeQueryDTO, KnowledgeResultDTO

logger = logging.getLogger(__name__)
KnowledgeEngine: Any | None = None
_IMPORT_ERROR: BaseException | None = None


class KnowledgeAdapter:
    """Bridge KnowledgeService calls to the frozen core knowledge engine."""

    def __init__(
        self,
        engine_factory: Callable[[], Any] | None = None,
        dataset_path: str = "output/knowledge_dataset.json",
    ) -> None:
        self._engine_factory = engine_factory
        self._dataset_path = dataset_path
        self._engine: Any | None = None
        self._last_error: str = ""

    def search(self, query: KnowledgeQueryDTO) -> list[KnowledgeResultDTO]:
        engine = self._get_engine()
        if engine is None:
            return []
        try:
            result = engine.query_text(query.text, k=query.limit)
            matches = list(read_attr(result, "matches", []) or [])
            return [self._result_from_core(match) for match in matches]
        except Exception as exc:
            logger.exception("Knowledge adapter search failed: %s", exc)
            self._last_error = safe_str(exc)
            return []

    def find_similar(self, name: str, entry_type: str) -> list[KnowledgeResultDTO]:
        engine = self._get_engine()
        if engine is None:
            return []
        try:
            method_name = f"find_similar_{entry_type.lower()}s"
            method = getattr(engine, method_name, engine.find_similar_hunts)
            return [self._result_from_core(item) for item in method(name, k=5)]
        except Exception as exc:
            logger.exception("Knowledge adapter similarity search failed: %s", exc)
            self._last_error = safe_str(exc)
            return []

    def get_metrics(self) -> KnowledgeMetricsDTO:
        engine = self._get_engine()
        if engine is None:
            return KnowledgeMetricsDTO(
                status=CORE_UNAVAILABLE,
                success=False,
                error_message=self._last_error,
            )
        dataset = getattr(engine, "dataset", None)
        entries = list(getattr(dataset, "entries", []) or [])
        return KnowledgeMetricsDTO(
            total_entries=len(entries),
            indexed_sources=1 if entries else 0,
            status="Loaded",
            success=True,
        )

    def _get_engine(self) -> Any | None:
        if self._engine is not None:
            return self._engine
        engine_class = self._load_engine_class()
        if _IMPORT_ERROR is not None or engine_class is None:
            self._last_error = safe_str(_IMPORT_ERROR) if _IMPORT_ERROR else CORE_UNAVAILABLE
            return None
        try:
            if self._engine_factory is not None:
                self._engine = self._engine_factory()
            elif Path(self._dataset_path).is_file():
                self._engine = engine_class.load(self._dataset_path)
            else:
                self._engine = engine_class()
            return self._engine
        except Exception as exc:
            logger.exception("Knowledge adapter failed to load core engine: %s", exc)
            self._last_error = safe_str(exc)
            return None

    def _result_from_core(self, item: Any) -> KnowledgeResultDTO:
        entry = read_attr(item, "entry", item)
        title = str(read_attr(entry, "name", read_attr(item, "name", "")))
        entry_type = read_attr(entry, "entry_type", read_attr(item, "entry_type", ""))
        return KnowledgeResultDTO(
            identifier=str(read_attr(entry, "id", title)),
            title=title,
            entry_type=str(read_attr(entry_type, "value", entry_type)),
            excerpt=str(read_attr(item, "match_type", "")),
            source=str(read_attr(entry, "source", "")),
            relevance=float(read_attr(item, "score", read_attr(item, "relevance", 0.0)) or 0.0),
        )

    @staticmethod
    def _load_engine_class() -> Any | None:
        global KnowledgeEngine, _IMPORT_ERROR
        if KnowledgeEngine is not None or _IMPORT_ERROR is not None:
            return KnowledgeEngine
        try:
            module = importlib.import_module("core.knowledge.knowledge_engine")
            KnowledgeEngine = getattr(module, "KnowledgeEngine")
        except Exception as exc:  # pragma: no cover - import failure path
            _IMPORT_ERROR = exc
            KnowledgeEngine = None
        return KnowledgeEngine
