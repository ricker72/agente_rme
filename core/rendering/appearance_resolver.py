"""
PMX-04R1 — Appearance resolver that maps ClientID → Appearance → Sprite Frames → Animation → Render Sprite.
Uses official appearance definitions already loaded.
"""

from __future__ import annotations

import time

from .appearance_loader import AppearanceLoader
from .appearance_models import AppearanceRecord, ResolvedSprite
from .sprite_resolver import SpriteResolver


class AppearanceResolver:
    """Resolves client IDs to appearance records and sprite frames.

    Pipeline:
    ClientID → Appearance → Sprite Frames → Animation → Render Sprite
    """

    def __init__(
        self,
        sprite_resolver: SpriteResolver | None = None,
        appearance_loader: AppearanceLoader | None = None,
    ) -> None:
        self.sprite_resolver = sprite_resolver or SpriteResolver()
        self.appearance_loader = appearance_loader or self.sprite_resolver.loader

        # Animation state
        self._animation_time: float = time.perf_counter()
        self._animation_frame: int = 0

    def resolve(self, item_id: int, client_id: int | None = None) -> ResolvedSprite:
        """Resolve an item/client ID to a ResolvedSprite."""
        return self.sprite_resolver.resolve(item_id, client_id)

    def resolve_asset(self, asset: object) -> ResolvedSprite:
        """Resolve an asset object to a ResolvedSprite."""
        return self.sprite_resolver.resolve_asset(asset)

    def get_appearance(self, appearance_id: int) -> AppearanceRecord | None:
        """Get the appearance record for an appearance ID."""
        return self.appearance_loader.record(appearance_id)

    def get_appearance_for_sprite(self, resolved: ResolvedSprite) -> AppearanceRecord | None:
        """Get the appearance record for a resolved sprite."""
        if resolved.appearance_id is None:
            return None
        return self.appearance_loader.record(resolved.appearance_id)

    def get_sprite_ids(self, resolved: ResolvedSprite) -> tuple[int, ...]:
        """Get all sprite IDs for a resolved sprite."""
        if resolved.sprite_ids:
            return resolved.sprite_ids
        appearance = self.get_appearance_for_sprite(resolved)
        if appearance is not None:
            return appearance.sprite_ids
        return ()

    def get_sprite_id(self, resolved: ResolvedSprite, frame: int = 0) -> int | None:
        """Get a specific sprite ID for a resolved sprite at a given frame."""
        sprite_ids = self.get_sprite_ids(resolved)
        if not sprite_ids:
            return None
        return sprite_ids[frame % len(sprite_ids)]

    def get_animation_frame_count(self, resolved: ResolvedSprite) -> int:
        """Get the number of animation frames for a resolved sprite."""
        appearance = self.get_appearance_for_sprite(resolved)
        if appearance is not None:
            return appearance.animation_frames
        return 1

    def get_current_animation_frame(self, resolved: ResolvedSprite) -> int:
        """Get the current animation frame based on elapsed time."""
        appearance = self.get_appearance_for_sprite(resolved)
        if appearance is None or appearance.animation_frames <= 1:
            return 0

        # Animate at ~4 fps (250ms per frame) like Tibia
        elapsed = time.perf_counter() - self._animation_time
        frame_duration = 0.25  # seconds per frame
        total_frames = appearance.animation_frames
        return int((elapsed / frame_duration) % total_frames)

    def get_sprite_size(self, resolved: ResolvedSprite) -> tuple[int, int]:
        """Get the sprite dimensions (width, height) in tiles."""
        appearance = self.get_appearance_for_sprite(resolved)
        if appearance is not None:
            return (appearance.width, appearance.height)
        return (1, 1)

    def get_pattern_info(self, resolved: ResolvedSprite) -> tuple[int, int, int]:
        """Get pattern dimensions (width, height, depth)."""
        appearance = self.get_appearance_for_sprite(resolved)
        if appearance is not None:
            return (appearance.pattern_width, appearance.pattern_height, appearance.pattern_depth)
        return (1, 1, 1)

    def update_animation(self) -> None:
        """Update the animation timer. Call once per frame."""
        self._animation_time = time.perf_counter()