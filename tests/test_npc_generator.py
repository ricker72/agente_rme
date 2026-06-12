from __future__ import annotations


from core.campaign.npc_generator import NPCGenerator, NPC


class TestNPCGeneratorInit:
    def test_create(self):
        gen = NPCGenerator()
        assert gen is not None


class TestNPCGeneratorRun:
    def test_generate_default(self):
        gen = NPCGenerator()
        npcs = gen.generate()
        assert len(npcs) == 8
        for npc in npcs:
            assert isinstance(npc, NPC)

    def test_generate_count(self):
        gen = NPCGenerator()
        npcs = gen.generate(count=5)
        assert len(npcs) == 5

    def test_generate_with_factions(self):
        gen = NPCGenerator()
        npcs = gen.generate(faction_names=["Crimson Guard", "Shadow Council"])
        for npc in npcs:
            assert npc.faction in ["Crimson Guard", "Shadow Council"]

    def test_generate_with_locations(self):
        gen = NPCGenerator()
        npcs = gen.generate(locations=["Temple", "Market", "Forest"])
        for npc in npcs:
            assert npc.location in ["Temple", "Market", "Forest"]

    def test_roles_distributed(self):
        gen = NPCGenerator()
        npcs = gen.generate(count=10)
        roles = {npc.role for npc in npcs}
        assert "quest_giver" in roles
        assert "merchant" in roles
        assert "enemy" in roles

    def test_enemies_have_higher_levels(self):
        gen = NPCGenerator()
        npcs = gen.generate(count=10)
        enemies = [n for n in npcs if n.role == "enemy"]
        merchants = [n for n in npcs if n.role == "merchant"]
        if enemies and merchants:
            assert enemies[0].combat_level > merchants[0].combat_level


class TestNPCGeneratorBoss:
    def test_generate_boss(self):
        gen = NPCGenerator()
        boss = gen.generate_boss("Demon Lord", "Evil Army", "Dark Fortress", 500)
        assert boss.name == "Demon Lord"
        assert boss.is_boss is True
        assert boss.combat_level == 500
        assert boss.role == "enemy"


class TestNPCData:
    def test_npc_to_dict(self):
        npc = NPC(name="Test", role="merchant", faction="TestFaction", combat_level=50)
        d = npc.to_dict()
        assert d["name"] == "Test"
        assert d["role"] == "merchant"
        assert d["combat_level"] == 50

    def test_npc_has_dialogue(self):
        gen = NPCGenerator()
        npcs = gen.generate(count=3)
        for npc in npcs:
            assert len(npc.dialogue_greeting) > 0
            assert len(npc.dialogue_farewell) > 0
