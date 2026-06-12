"""
Conftest for UI tests - provides QApplication fixture.
"""

import pytest


@pytest.fixture(scope="session")
def qapp_instance():
    """Create a QApplication instance for widget tests."""
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
