from __future__ import annotations


from core.campaign.lore_generator import LoreGenerator, LoreEntry


class TestLoreGeneratorInit:
    def test_create(self):
        gen = LoreGenerator()
        assert gen is not None


class TestLoreGeneratorRun:
    def test_generate_default(self):
        gen = LoreGenerator()
        entries = gen.generate()
        assert len(entries) == 5
        for entry in entries:
            assert isinstance(entry, LoreEntry)

    def test_generate_issavi(self):
        gen = LoreGenerator()
        entries = gen.generate(theme="Issavi", count=3)
        assert len(entries) == 3
        assert entries[0].title == "The Fall of Issavi"

    def test_generate_darashia(self):
        gen = LoreGenerator()
        entries = gen.generate(theme="Darashia")
        assert len(entries) >= 2

    def test_generate_with_factions(self):
        gen = LoreGenerator()
        entries = gen.generate(faction_names=["Guard", "Council"], count=4)
        assert len(entries) == 4
        for entry in entries:
            assert entry.related_factions is not None

    def test_generate_count(self):
        gen = LoreGenerator()
        entries = gen.generate(count=2)
        assert len(entries) == 2

    def test_generate_more_than_templates(self):
        gen = LoreGenerator()
        entries = gen.generate(theme="Issavi", count=10)
        assert len(entries) == 10


class TestLoreGeneratorSpecial:
    def test_generate_prophecy(self):
        gen = LoreGenerator()
        p = gen.generate_prophecy("Issavi", factions=["Guard", "Council"])
        assert p.category == "prophecy"
        assert p.importance == 5
        assert "Issavi" in p.title
        assert "Guard" in p.related_factions

    def test_generate_prophecy_no_factions(self):
        gen = LoreGenerator()
        p = gen.generate_prophecy("Darashia")
        assert p.category == "prophecy"

    def test_generate_secret(self):
        gen = LoreGenerator()
        s = gen.generate_secret("Roshamuul", npc_name="Scholar Voss")
        assert s.category == "secret"
        assert "Scholar Voss" in s.related_npcs

    def test_generate_secret_no_npc(self):
        gen = LoreGenerator()
        s = gen.generate_secret("Default")
        assert s.category == "secret"
        assert len(s.related_npcs) == 0


class TestLoreEntryData:
    def test_to_dict(self):
        entry = LoreEntry(
            title="Test", category="history", content="Content", importance=3
        )
        d = entry.to_dict()
        assert d["title"] == "Test"
        assert d["category"] == "history"
        assert d["importance"] == 3

    def test_entries_have_importance(self):
        gen = LoreGenerator()
        entries = gen.generate()
        for entry in entries:
            assert 1 <= entry.importance <= 5

    def test_entries_have_categories(self):
        gen = LoreGenerator()
        entries = gen.generate()
        valid = {"history", "myth", "legend", "prophecy", "secret"}
        for entry in entries:
            assert entry.category in valid
