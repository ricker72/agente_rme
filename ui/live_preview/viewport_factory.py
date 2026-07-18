from __future__ import annotations

import os

from PySide6.QtGui import QGuiApplication

from .viewport_widget import ViewportWidget


def create_rme_viewport():
    """Create the preferred live map viewport, using OpenGL when safe."""

    if os.environ.get("RME_AI_DISABLE_GL_VIEWPORT") == "1":
        return ViewportWidget()
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return ViewportWidget()
    app = QGuiApplication.instance()
    platform = app.platformName().lower() if app is not None else ""
    if platform in {"offscreen", "minimal"}:
        return ViewportWidget()
    try:
        from .rme_gl_viewport import RMEGLViewportWidget

        return RMEGLViewportWidget()
    except Exception:
        return ViewportWidget()
