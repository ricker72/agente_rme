"""
Tests for ServiceContainer.

Validates dependency injection: singleton registry, factory registration,
lazy resolution, runtime replacement, mock replacement, and thread safety.
"""

from __future__ import annotations


import pytest

from ui.services.service_container import ServiceContainer
from ui.services.null_services import NullDashboardService, NullWorldService
from ui.services.service_exceptions import ServiceNotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def container() -> ServiceContainer:
    """Return a fresh empty container for each test."""
    return ServiceContainer()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestContainerRegistration:
    def test_register_instance(self, container: ServiceContainer) -> None:
        mock = {"name": "test-service"}
        container.register("test", mock)
        assert container.has("test")
        assert container.resolve("test") is mock

    def test_register_duplicate_raises(self, container: ServiceContainer) -> None:
        container.register("dup", object())
        with pytest.raises(RuntimeError):
            container.register("dup", object())

    def test_register_force_replaces(self, container: ServiceContainer) -> None:
        container.register("svc", "original")
        container.register("svc", "replacement", force=True)
        assert container.resolve("svc") == "replacement"

    def test_register_factory(self, container: ServiceContainer) -> None:
        container.register("factory", lambda: {"lazy": True})
        assert container.has("factory")
        result: dict[str, bool] = container.resolve("factory")  # type: ignore[assignment]
        assert result == {"lazy": True}

    def test_factory_called_once(self, container: ServiceContainer) -> None:
        call_count: list[int] = [0]

        def factory() -> dict[str, int]:
            call_count[0] += 1
            return {"count": call_count[0]}

        container.register_factory("single", factory)
        r1: dict[str, int] = container.resolve("single")  # type: ignore[assignment]
        r2: dict[str, int] = container.resolve("single")  # type: ignore[assignment]
        assert r1 is r2
        assert call_count[0] == 1


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


class TestContainerResolution:
    def test_resolve_existing(self, container: ServiceContainer) -> None:
        container.register("svc", {"service": "data"})
        assert container.resolve("svc") == {"service": "data"}

    def test_resolve_missing_raises(self, container: ServiceContainer) -> None:
        with pytest.raises(ServiceNotFoundError):
            container.resolve("ghost")

    def test_resolve_or_none_exists(self, container: ServiceContainer) -> None:
        container.register("svc", "exists")
        assert container.resolve_or_none("svc") == "exists"

    def test_resolve_or_none_missing(self, container: ServiceContainer) -> None:
        assert container.resolve_or_none("ghost") is None


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestContainerLifecycle:
    def test_unregister_removes(self, container: ServiceContainer) -> None:
        container.register("tmp", object())
        assert container.has("tmp")
        container.unregister("tmp")
        assert not container.has("tmp")

    def test_unregister_missing_noop(self, container: ServiceContainer) -> None:
        container.unregister("does_not_exist")

    def test_clear_removes_all(self, container: ServiceContainer) -> None:
        container.register("a", object())
        container.register_factory("b", lambda: None)
        container.clear()
        assert len(container.keys()) == 0

    def test_contains(self, container: ServiceContainer) -> None:
        container.register("present", object())
        assert "present" in container
        assert "absent" not in container

    def test_keys(self, container: ServiceContainer) -> None:
        container.register("x", 1)
        container.register_factory("y", lambda: 2)
        keys = container.keys()
        assert "x" in keys
        assert "y" in keys


# ---------------------------------------------------------------------------
# Mock / Test replacement
# ---------------------------------------------------------------------------


class TestMockReplacement:
    def test_register_mock_replaces(self, container: ServiceContainer) -> None:
        real = {"real": True}
        container.register("svc", real)
        mock = {"mock": True}
        container.register_mock("svc", mock)
        assert container.resolve("svc") is mock

    def test_register_mock_new(self, container: ServiceContainer) -> None:
        mock = {"mock": True}
        container.register_mock("new_svc", mock)
        assert container.resolve("new_svc") is mock

    def test_mock_replacements_isolated(self, container: ServiceContainer) -> None:
        container.register("a", "real_a")
        container.register("b", "real_b")
        container.register_mock("a", "mock_a")
        assert container.resolve("a") == "mock_a"
        assert container.resolve("b") == "real_b"


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    def test_concurrent_registration(self, container: ServiceContainer) -> None:
        """Verify that concurrent registrations don't deadlock."""
        import threading

        results: list[Exception | None] = [None, None]

        def register_a() -> None:
            try:
                container.register("a", "value_a")
            except Exception as exc:
                results[0] = exc

        def register_b() -> None:
            try:
                container.register("b", "value_b")
            except Exception as exc:
                results[1] = exc

        t1 = threading.Thread(target=register_a)
        t2 = threading.Thread(target=register_b)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert results[0] is None
        assert results[1] is None
        assert container.resolve("a") == "value_a"
        assert container.resolve("b") == "value_b"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestContainerEdgeCases:
    def test_repr(self, container: ServiceContainer) -> None:
        container.register("svc", "value")
        text = repr(container)
        assert "ServiceContainer" in text
        assert "svc" in text

    def test_register_none(self, container: ServiceContainer) -> None:
        container.register("none", None)  # type: ignore[arg-type]
        assert container.resolve("none") is None

    def test_empty_container_has_no_keys(self, container: ServiceContainer) -> None:
        assert container.keys() == []


class TestDefaultServices:
    def test_register_defaults_adds_all_services(self, container: ServiceContainer) -> None:
        container.register_defaults()
        assert container.keys() == [
            "autonomous",
            "campaign",
            "critic",
            "dashboard",
            "knowledge",
            "otbm",
            "world",
        ]

    def test_typed_getters_return_defaults(self, container: ServiceContainer) -> None:
        container.register_defaults()
        assert isinstance(container.get_world_service(), NullWorldService)
        assert isinstance(container.get_dashboard_service(), NullDashboardService)

    def test_override_default_for_tests(self, container: ServiceContainer) -> None:
        fake = object()
        container.register_defaults()
        container.register_mock(ServiceContainer.WORLD, fake)
        assert container.get_world_service() is fake
