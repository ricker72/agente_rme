"""Core-backed world adapter."""

from __future__ import annotations

import logging
import importlib
from typing import Any, Callable

from ui.adapters._helpers import CORE_EXECUTION_FAILED, CORE_UNAVAILABLE, count_tiles, safe_str
from ui.models.world_dto import WorldDTO, WorldGenerationRequestDTO, WorldSummaryDTO

logger = logging.getLogger(__name__)
WorldGenerator: Any | None = None
_IMPORT_ERROR: BaseException | None = None


class WorldAdapter:
    """Bridge WorldService calls to the frozen core world generator."""

    def __init__(self, generator_factory: Callable[[int | None], Any] | None = None) -> None:
        self._generator_factory = generator_factory
        self._recent_worlds: list[WorldDTO] = []

    def generate_world(self, request: WorldGenerationRequestDTO) -> WorldDTO:
        generator_class = self._load_generator_class()
        if _IMPORT_ERROR is not None or generator_class is None:
            return self._world_failure(CORE_UNAVAILABLE, _IMPORT_ERROR)
        try:
            factory = self._generator_factory or generator_class
            generator = factory(request.seed)
            world = generator.generate(self._request_to_core(request))
            dto = self._world_from_core(world, request)
            self._recent_worlds.insert(0, dto)
            self._recent_worlds = self._recent_worlds[:10]
            return dto
        except Exception as exc:
            logger.exception("World adapter failed to generate world: %s", exc)
            return self._world_failure(CORE_EXECUTION_FAILED, exc)

    def get_recent_worlds(self) -> list[WorldDTO]:
        return list(self._recent_worlds)

    def get_world_summary(self, world_id: str) -> WorldSummaryDTO:
        for world in self._recent_worlds:
            if world.world_id == world_id:
                return WorldSummaryDTO(
                    world_id=world.world_id,
                    name=world.name,
                    size_label=f"{world.width}x{world.height}",
                    status=world.status,
                    success=world.success,
                )
        return WorldSummaryDTO(
            world_id=world_id,
            status="Not found",
            success=False,
            error_message=f"World '{world_id}' is not available in adapter cache",
        )

    def _request_to_core(self, request: WorldGenerationRequestDTO) -> dict[str, Any]:
        return {
            "name": request.name,
            "width": request.width,
            "height": request.height,
            "theme": request.theme or "generic",
            "seed": request.seed,
            "constraints": list(request.constraints),
        }

    def _world_from_core(self, world: Any, request: WorldGenerationRequestDTO) -> WorldDTO:
        width = int(getattr(world, "width", request.width or 0) or request.width or 0)
        height = int(getattr(world, "height", request.height or 0) or request.height or 0)
        world_id = str(getattr(world, "world_id", "") or getattr(world, "id", "") or request.name)
        return WorldDTO(
            world_id=world_id,
            name=request.name or world_id or "Generated world",
            width=width,
            height=height,
            description=f"{count_tiles(world)} tiles generated",
            status="Generated",
            success=True,
        )

    @staticmethod
    def _world_failure(status: str, error: BaseException | None) -> WorldDTO:
        message = safe_str(error) if error is not None else status
        return WorldDTO(status=status, success=False, error_message=message)

    @staticmethod
    def _load_generator_class() -> Any | None:
        global WorldGenerator, _IMPORT_ERROR
        if WorldGenerator is not None or _IMPORT_ERROR is not None:
            return WorldGenerator
        try:
            module = importlib.import_module("core.generators.world_generator")
            WorldGenerator = getattr(module, "WorldGenerator")
        except Exception as exc:  # pragma: no cover - import failure path
            _IMPORT_ERROR = exc
            WorldGenerator = None
        return WorldGenerator
