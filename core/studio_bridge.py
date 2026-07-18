from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.playtest import PlaytestEngine
    from core.preview import PreviewGenerator
else:
    PlaytestEngine = Any
    PreviewGenerator = Any


class PlaytestRunner:
    def __init__(self, engine: PlaytestEngine) -> None:
        self._engine = engine

    def run(
        self,
        world_model: Any,
        theme: str,
        level_range: str,
        dps_estimator: Any,
    ) -> dict[str, object]:
        zones = getattr(world_model, "spawns", [])
        if not zones:
            return {"routes": [], "summary": "No spawn zones available for playtest."}
        return self._engine.run_world_playtest(
            world_model=world_model,
            theme=theme,
            level_range=level_range,
            player_dps=dps_estimator(level_range),
        )


class PreviewRunner:
    def __init__(self, generator: PreviewGenerator) -> None:
        self._generator = generator

    def build(self, world_model: Any) -> dict[str, object]:
        return self._generator.generate(world_model=world_model)