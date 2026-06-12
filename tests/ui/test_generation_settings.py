"""Tests for generation settings and prompt widgets."""

from __future__ import annotations

from ui.widgets.generation_settings_panel import GenerationSettingsPanel
from ui.widgets.world_prompt_panel import WorldPromptPanel


def test_generation_settings_defaults(qapp_instance: object) -> None:
    panel = GenerationSettingsPanel()
    settings = panel.settings()
    assert settings.size == "Medium"
    assert settings.theme == "Issavi"
    assert settings.min_level == 300
    assert settings.max_level == 500
    assert settings.mode == "Standard"
    assert panel.dimensions() == (256, 256)
    assert panel.is_valid()


def test_generation_settings_validation(qapp_instance: object) -> None:
    panel = GenerationSettingsPanel()
    panel.min_level_spin.setValue(700)
    panel.max_level_spin.setValue(300)
    assert not panel.is_valid()


def test_prompt_panel_validation_and_counter(qapp_instance: object) -> None:
    panel = WorldPromptPanel()
    panel.set_prompt("Issavi")
    assert not panel.is_valid()
    panel.set_prompt("Create an Issavi expansion")
    assert panel.is_valid()
    assert "26 characters" in panel.counter_label.text()
