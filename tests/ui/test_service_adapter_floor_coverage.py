from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from ui.adapters import knowledge_adapter
from ui.adapters._helpers import count_tiles, read_attr, safe_str
from ui.adapters.knowledge_adapter import KnowledgeAdapter
from ui.models.autonomous_dto import AutonomousDesignRequestDTO
from ui.models.campaign_dto import CampaignRequestDTO
from ui.models.critic_dto import CriticRequestDTO
from ui.models.knowledge_dto import KnowledgeQueryDTO
from ui.models.otbm_dto import OTBMExportRequestDTO
from ui.models.world_dto import WorldGenerationRequestDTO
from ui.services.autonomous_service import AutonomousService
from ui.services.base_service import BaseService
from ui.services.campaign_service import CampaignService
from ui.services.critic_service import CriticService
from ui.services.dashboard_service import DashboardService
from ui.services.knowledge_service import KnowledgeService
from ui.services.otbm_service import OTBMService
from ui.services.world_service import WorldService


class TileCountWorld:
    def tile_count(self) -> str:
        return "12"


class TilesWorld:
    tiles = [1, 2, 3]


class BadTilesWorld:
    class BadTiles:
        def __len__(self) -> int:
            raise TypeError("no len")

    tiles = BadTiles()


def test_adapter_helpers_defensive_branches() -> None:
    assert safe_str(RuntimeError()) == "RuntimeError"
    assert read_attr({"name": "value"}, "name") == "value"
    assert read_attr(object(), "missing", "fallback") == "fallback"
    assert count_tiles(TileCountWorld()) == 12
    assert count_tiles(TilesWorld()) == 3
    assert count_tiles(BadTilesWorld()) == 0
    assert count_tiles(object()) == 0


class SearchFailingEngine:
    dataset = None

    def query_text(self, text: str, k: int = 5) -> object:
        raise RuntimeError("search failed")

    def find_similar_hunts(self, name: str, k: int = 5) -> list[object]:
        return []


class SimilarityEngine:
    dataset = None

    def query_text(self, text: str, k: int = 5) -> object:
        return type("Result", (), {"matches": []})()

    def find_similar_hunts(self, name: str, k: int = 5) -> list[dict[str, object]]:
        return [{"name": name, "score": 0.25, "entry_type": "hunt"}]

    def find_similar_quests(self, name: str, k: int = 5) -> list[dict[str, object]]:
        return [{"name": name, "score": 0.75, "entry_type": "quest"}]


class SimilarityFailingEngine(SimilarityEngine):
    def find_similar_hunts(self, name: str, k: int = 5) -> list[dict[str, object]]:
        raise RuntimeError("similarity failed")


class LoadableEngine(SimilarityEngine):
    loaded_path = ""

    @classmethod
    def load(cls, path: str) -> "LoadableEngine":
        cls.loaded_path = path
        return cls()


def test_knowledge_adapter_failure_and_similarity_paths(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(knowledge_adapter, "_IMPORT_ERROR", None)
    monkeypatch.setattr(knowledge_adapter, "KnowledgeEngine", LoadableEngine)

    search_adapter = KnowledgeAdapter(engine_factory=SearchFailingEngine)
    assert search_adapter.search(KnowledgeQueryDTO(text="x")) == []
    assert search_adapter._last_error == "search failed"

    adapter = KnowledgeAdapter(engine_factory=SimilarityEngine)
    fallback = adapter.find_similar("rotworm", "hunt")
    specific = adapter.find_similar("questline", "quest")
    assert fallback[0].title == "rotworm"
    assert fallback[0].relevance == 0.25
    assert specific[0].entry_type == "quest"
    assert adapter.search(KnowledgeQueryDTO(text="empty")) == []

    failing = KnowledgeAdapter(engine_factory=SimilarityFailingEngine)
    assert failing.find_similar("rotworm", "hunt") == []
    assert failing._last_error == "similarity failed"


def test_knowledge_adapter_engine_loading_paths(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(knowledge_adapter, "_IMPORT_ERROR", None)
    monkeypatch.setattr(knowledge_adapter, "KnowledgeEngine", LoadableEngine)
    dataset = tmp_path / "knowledge.json"
    dataset.write_text("{}", encoding="utf-8")

    from_file = KnowledgeAdapter(dataset_path=str(dataset))
    assert isinstance(from_file._get_engine(), LoadableEngine)
    assert LoadableEngine.loaded_path == str(dataset)

    constructed = KnowledgeAdapter(dataset_path=str(tmp_path / "missing.json"))
    assert isinstance(constructed._get_engine(), LoadableEngine)
    assert constructed._get_engine() is constructed._engine

    def explode() -> object:
        raise RuntimeError("factory failed")

    broken = KnowledgeAdapter(engine_factory=explode)
    assert broken._get_engine() is None
    assert broken._last_error == "factory failed"


def test_knowledge_adapter_import_loader_success_and_failure(monkeypatch: MonkeyPatch) -> None:
    class Module:
        KnowledgeEngine = LoadableEngine

    monkeypatch.setattr(knowledge_adapter, "KnowledgeEngine", None)
    monkeypatch.setattr(knowledge_adapter, "_IMPORT_ERROR", None)
    monkeypatch.setattr(knowledge_adapter.importlib, "import_module", lambda name: Module)
    assert KnowledgeAdapter._load_engine_class() is LoadableEngine

    def fail_import(name: str) -> object:
        raise ImportError("missing core")

    monkeypatch.setattr(knowledge_adapter, "KnowledgeEngine", None)
    monkeypatch.setattr(knowledge_adapter, "_IMPORT_ERROR", None)
    monkeypatch.setattr(knowledge_adapter.importlib, "import_module", fail_import)
    assert KnowledgeAdapter._load_engine_class() is None
    assert isinstance(knowledge_adapter._IMPORT_ERROR, ImportError)


class ServiceContractTarget:
    service_name = "target"

    def is_connected(self) -> bool:
        return True


def test_protocol_stub_bodies_are_executable_interface_noops() -> None:
    target = ServiceContractTarget()

    assert BaseService.service_name.fget(target) is None  # type: ignore[attr-defined]
    assert BaseService.is_connected(target) is None
    assert WorldService.generate_world(target, WorldGenerationRequestDTO()) is None  # type: ignore[arg-type]
    assert WorldService.get_recent_worlds(target) is None  # type: ignore[arg-type]
    assert WorldService.get_world_summary(target, "w1") is None  # type: ignore[arg-type]
    assert CampaignService.generate_campaign(target, CampaignRequestDTO()) is None  # type: ignore[arg-type]
    assert CampaignService.get_last_campaign(target) is None  # type: ignore[arg-type]
    assert DashboardService.load_dashboard(target) is None  # type: ignore[arg-type]
    assert DashboardService.refresh_dashboard(target) is None  # type: ignore[arg-type]
    assert AutonomousService.run_design(target, AutonomousDesignRequestDTO()) is None  # type: ignore[arg-type]
    assert AutonomousService.get_iterations(target) is None  # type: ignore[arg-type]
    assert AutonomousService.get_metrics(target) is None  # type: ignore[arg-type]
    assert CriticService.analyze_world(target, CriticRequestDTO()) is None  # type: ignore[arg-type]
    assert CriticService.get_last_report(target) is None  # type: ignore[arg-type]
    assert CriticService.get_heatmaps(target) is None  # type: ignore[arg-type]
    assert KnowledgeService.search(target, KnowledgeQueryDTO()) is None  # type: ignore[arg-type]
    assert KnowledgeService.find_similar(target, "orc", "hunt") is None  # type: ignore[arg-type]
    assert KnowledgeService.get_metrics(target) is None  # type: ignore[arg-type]
    assert OTBMService.import_otbm(target, "in.otbm") is None  # type: ignore[arg-type]
    assert OTBMService.export_otbm(target, OTBMExportRequestDTO()) is None  # type: ignore[arg-type]
    assert OTBMService.validate_otbm(target, "in.otbm") is None  # type: ignore[arg-type]
