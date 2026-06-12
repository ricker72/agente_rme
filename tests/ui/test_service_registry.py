"""
Tests for ServiceRegistry.

Validates registration, resolution, factory support, error handling,
and lifecycle management.
"""

from __future__ import annotations

from typing import Any

import pytest

from ui.services.service_registry import (
    ServiceRegistry,
)
from ui.services.service_exceptions import (
    ServiceAlreadyRegisteredError,
    ServiceNotFoundError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def registry() -> ServiceRegistry[Any]:
    """Return a fresh empty registry for each test."""
    return ServiceRegistry()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_instance(self, registry: ServiceRegistry[Any]) -> None:
        mock = object()
        registry.register("test", mock)
        assert registry.has("test")
        assert registry.resolve("test") is mock

    def test_register_duplicate_raises(self, registry: ServiceRegistry[Any]) -> None:
        registry.register("dup", object())
        with pytest.raises(ServiceAlreadyRegisteredError) as exc:
            registry.register("dup", object())
        assert "dup" in str(exc.value)

    def test_register_duplicate_force(self, registry: ServiceRegistry[Any]) -> None:
        mock_a = object()
        mock_b = object()
        registry.register("dup", mock_a)
        registry.register("dup", mock_b, force=True)
        assert registry.resolve("dup") is mock_b

    def test_register_factory(self, registry: ServiceRegistry[Any]) -> None:
        registry.register("factory", lambda: {"created": True})
        assert registry.has("factory")
        result = registry.resolve("factory")
        assert result == {"created": True}

    def test_factory_called_once(self, registry: ServiceRegistry[Any]) -> None:
        call_count: list[int] = [0]

        def factory() -> dict[str, int]:
            call_count[0] += 1
            return {"count": call_count[0]}

        registry.register_factory("single", factory)
        r1 = registry.resolve("single")
        r2 = registry.resolve("single")
        assert r1 is r2
        assert call_count[0] == 1

    def test_factory_resolves_after_instance(
        self, registry: ServiceRegistry[Any]
    ) -> None:
        registry.register("svc", object())
        registry.register_factory("factory", lambda: {"ok": True})
        assert registry.has("svc")
        assert registry.has("factory")

    def test_register_factory_duplicate_raises(
        self, registry: ServiceRegistry[Any]
    ) -> None:
        registry.register_factory("dup", lambda: None)
        with pytest.raises(ServiceAlreadyRegisteredError):
            registry.register_factory("dup", lambda: None)

    def test_register_factory_duplicate_force(
        self, registry: ServiceRegistry[Any]
    ) -> None:
        registry.register_factory("dup", lambda: "a")
        registry.register_factory("dup", lambda: "b", force=True)
        assert registry.resolve("dup") == "b"


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


class TestResolution:
    def test_resolve_existing(self, registry: ServiceRegistry[Any]) -> None:
        mock = {"service": "alive"}
        registry.register("alive", mock)
        assert registry.resolve("alive") is mock

    def test_resolve_missing_raises(self, registry: ServiceRegistry[Any]) -> None:
        with pytest.raises(ServiceNotFoundError) as exc:
            registry.resolve("ghost")
        assert "ghost" in str(exc.value)

    def test_resolve_factory_lazy(self, registry: ServiceRegistry[Any]) -> None:
        registry.register_factory("lazy", lambda: "lazy_value")
        assert registry.resolve("lazy") == "lazy_value"


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_unregister_removes_instance(self, registry: ServiceRegistry[Any]) -> None:
        registry.register("tmp", object())
        assert registry.has("tmp")
        registry.unregister("tmp")
        assert not registry.has("tmp")
        with pytest.raises(ServiceNotFoundError):
            registry.resolve("tmp")

    def test_unregister_missing_is_noop(self, registry: ServiceRegistry[Any]) -> None:
        registry.unregister("does_not_exist")  # should not raise

    def test_clear_removes_all(self, registry: ServiceRegistry[Any]) -> None:
        registry.register("a", object())
        registry.register("b", object())
        registry.register_factory("c", lambda: None)
        registry.clear()
        assert len(registry) == 0
        assert not registry.has("a")

    def test_keys_returns_all_names(self, registry: ServiceRegistry[Any]) -> None:
        registry.register("x", object())
        registry.register_factory("y", lambda: None)
        keys = registry.keys()
        assert "x" in keys
        assert "y" in keys

    def test_contains(self, registry: ServiceRegistry[Any]) -> None:
        registry.register("present", object())
        assert "present" in registry
        assert "absent" not in registry


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_register_none(self, registry: ServiceRegistry[Any]) -> None:
        """Should allow registering None as a valid service."""
        registry.register("none", None)  # type: ignore[arg-type]
        assert registry.has("none")
        assert registry.resolve("none") is None

    def test_empty_registry_len_zero(self, registry: ServiceRegistry[Any]) -> None:
        assert len(registry) == 0

    def test_repr(self, registry: ServiceRegistry[Any]) -> None:
        registry.register("s1", object())
        registry.register_factory("s2", lambda: None)
        text = repr(registry)
        assert "ServiceRegistry" in text
        assert "s1" in text
        assert "s2" in text

    def test_register_overwrites_factory_with_instance(
        self, registry: ServiceRegistry[Any]
    ) -> None:
        registry.register_factory("name", lambda: "from_factory")
        registry.register("name", "from_instance", force=True)
        assert registry.resolve("name") == "from_instance"
