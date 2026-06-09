from __future__ import annotations

import pytest
import json
import tempfile
import os

from core.campaign.campaign_generator import CampaignGenerator, Campaign


class TestCampaignGeneratorInit:
    def test_create(self):
        gen = CampaignGenerator()
        assert gen is not None

    def test_has_all_subgenerators(self):
        gen = CampaignGenerator()
        assert gen._lore_gen is not None
        assert gen._npc_gen is not None
        assert gen._faction_gen is not None
        assert gen._story_gen is not None
        assert gen._dialog_gen is not None
        assert gen._economy_gen is not None


class TestCampaignGeneratorRun:
    def test_generate_default(self):
        gen = CampaignGenerator()
        campaign = gen.generate()
        assert isinstance(campaign, Campaign)
        assert campaign.theme == "default"
        assert len(campaign.lore) > 0
        assert len(campaign.factions) > 0
        assert len(campaign.npcs) > 0

    def test_generate_issavi(self):
        gen = CampaignGenerator()
        campaign = gen.generate(theme="Issavi", level_range=(300, 500))
        assert campaign.theme == "Issavi"
        assert campaign.main_story is not None
        assert len(campaign.main_story["chapters"]) >= 1
        assert campaign.level_range == (300, 500)

    def test_generate_has_name(self):
        gen = CampaignGenerator()
        campaign = gen.generate(theme="Darashia")
        assert "Darashia" in campaign.name

    def test_generate_has_factions(self):
        gen = CampaignGenerator()
        campaign = gen.generate(faction_count=5)
        assert len(campaign.factions) >= 3

    def test_generate_has_npcs(self):
        gen = CampaignGenerator()
        campaign = gen.generate(npc_count=12)
        assert len(campaign.npcs) >= 8

    def test_generate_has_economy(self):
        gen = CampaignGenerator()
        campaign = gen.generate()
        assert campaign.economy is not None
        assert "currency_name" in campaign.economy

    def test_generate_has_dialogs(self):
        gen = CampaignGenerator()
        campaign = gen.generate(npc_count=5)
        assert len(campaign.dialogs) > 0

    def test_generate_has_bosses(self):
        gen = CampaignGenerator()
        campaign = gen.generate()
        assert len(campaign.bosses) > 0

    def test_generate_has_raids(self):
        gen = CampaignGenerator()
        campaign = gen.generate()
        assert len(campaign.raids) > 0

    def test_generate_has_side_quests(self):
        gen = CampaignGenerator()
        campaign = gen.generate()
        assert len(campaign.side_quests) > 0


class TestCampaignSerialization:
    def test_to_dict(self):
        gen = CampaignGenerator()
        campaign = gen.generate(theme="Issavi")
        d = campaign.to_dict()
        assert "theme" in d
        assert "lore" in d
        assert "factions" in d
        assert "npcs" in d
        assert "main_story" in d

    def test_to_json(self):
        gen = CampaignGenerator()
        campaign = gen.generate()
        j = campaign.to_json()
        data = json.loads(j)
        assert data["theme"] == "default"
        assert isinstance(data["lore"], list)

    def test_save_and_load(self):
        gen = CampaignGenerator()
        campaign = gen.generate(theme="Roshamuul")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                          delete=False) as f:
            path = f.name

        try:
            gen.save(campaign, path)
            loaded = gen.load(path)
            assert loaded.theme == "Roshamuul"
            assert len(loaded.lore) == len(campaign.lore)
            assert len(loaded.factions) == len(campaign.factions)
        finally:
            os.unlink(path)


class TestCampaignDataIntegrity:
    def test_lore_has_required_fields(self):
        gen = CampaignGenerator()
        campaign = gen.generate()
        for entry in campaign.lore:
            assert "title" in entry
            assert "category" in entry
            assert "content" in entry

    def test_factions_have_relationships(self):
        gen = CampaignGenerator()
        campaign = gen.generate(faction_count=3)
        has_allies_or_enemies = False
        for f in campaign.factions:
            if f.get("allied_factions") or f.get("enemy_factions"):
                has_allies_or_enemies = True
        assert has_allies_or_enemies

    def test_npcs_have_dialogue(self):
        gen = CampaignGenerator()
        campaign = gen.generate(npc_count=4)
        for npc in campaign.npcs:
            assert "dialogue_greeting" in npc
            assert len(npc["dialogue_greeting"]) > 0

    def test_bosses_have_level(self):
        gen = CampaignGenerator()
        campaign = gen.generate()
        for boss in campaign.bosses:
            assert boss["level"] > 0