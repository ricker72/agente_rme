"""
MAP-01B: NECRO Viewport Navigation
Viewport interaction and navigation for OpenTibia mapping
"""

from typing import Tuple
import sys
import types

try:
    import pygame  # type: ignore[import-not-found]
except ModuleNotFoundError:
    class _FallbackEvent:
        def __init__(self, event_type: int, **kwargs):
            self.type = event_type
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _FallbackEventModule:
        @staticmethod
        def Event(event_type: int, **kwargs):
            return _FallbackEvent(event_type, **kwargs)

    class _FallbackMouseModule:
        _position = (0, 0)

        @classmethod
        def get_pos(cls):
            return cls._position

    pygame = types.SimpleNamespace(  # type: ignore[assignment]
        MOUSEWHEEL=1,
        MOUSEBUTTONDOWN=2,
        MOUSEBUTTONUP=3,
        MOUSEMOTION=4,
        event=_FallbackEventModule(),
        mouse=_FallbackMouseModule(),
    )
    sys.modules["pygame"] = pygame

class Viewport:
    """Viewport for navigating NECRO map"""

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 4.0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_viewport_x = 0
        self.drag_viewport_y = 0
        self.show_grid = True
        self.show_coordinates = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events for viewport navigation"""
        handled = False

        if event.type == pygame.MOUSEWHEEL:
            # Zoom with mouse wheel
            old_zoom = self.zoom
            if event.y > 0:
                self.zoom = min(self.zoom * 1.1, self.max_zoom)
            else:
                self.zoom = max(self.zoom * 0.9, self.min_zoom)

            # Adjust position to zoom toward mouse cursor
            if old_zoom != self.zoom:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                world_x, world_y = self.screen_to_world(mouse_x, mouse_y)

                self.x = world_x - (mouse_x / self.zoom)
                self.y = world_y - (mouse_y / self.zoom)
                handled = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button
                self.dragging = True
                self.drag_start_x, self.drag_start_y = getattr(event, "pos", pygame.mouse.get_pos())
                self.drag_viewport_x = self.x
                self.drag_viewport_y = self.y
                handled = True
            elif event.button == 3:  # Right mouse button
                # Jump to clicked coordinate
                mouse_x, mouse_y = getattr(event, "pos", pygame.mouse.get_pos())
                world_x, world_y = self.screen_to_world(mouse_x, mouse_y)
                self.x = world_x - (self.width / 2 / self.zoom)
                self.y = world_y - (self.height / 2 / self.zoom)
                handled = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:  # Middle mouse button
                self.dragging = False
                handled = True

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, mouse_y = getattr(event, "pos", pygame.mouse.get_pos())
                dx = (mouse_x - self.drag_start_x) / self.zoom
                dy = (mouse_y - self.drag_start_y) / self.zoom
                self.x = self.drag_viewport_x - dx
                self.y = self.drag_viewport_y - dy
                handled = True

        return handled

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        world_x = self.x + (screen_x / self.zoom)
        world_y = self.y + (screen_y / self.zoom)
        return world_x, world_y

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.x) * self.zoom
        screen_y = (world_y - self.y) * self.zoom
        return screen_x, screen_y

    def get_visible_area(self) -> Tuple[float, float, float, float]:
        """Get visible world area (min_x, min_y, max_x, max_y)"""
        min_x, min_y = self.screen_to_world(0, 0)
        max_x, max_y = self.screen_to_world(self.width, self.height)
        return min_x, min_y, max_x, max_y

    def jump_to_coordinate(self, x: float, y: float):
        """Center viewport on specific world coordinate"""
        self.x = x - (self.width / 2 / self.zoom)
        self.y = y - (self.height / 2 / self.zoom)

    def get_status(self) -> dict:
        """Get current viewport status"""
        min_x, min_y, max_x, max_y = self.get_visible_area()
        return {
            'position': (self.x, self.y),
            'zoom': self.zoom,
            'visible_area': (min_x, min_y, max_x, max_y),
            'grid_visible': self.show_grid,
            'coordinates_visible': self.show_coordinates
        }

    def toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid = not self.show_grid

    def toggle_coordinates(self):
        """Toggle coordinate overlay visibility"""
        self.show_coordinates = not self.show_coordinates

    def reset_view(self):
        """Reset viewport to default position and zoom"""
        self.x = 0
        self.y = 0
        self.zoom = 1.0
