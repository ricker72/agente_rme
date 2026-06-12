from __future__ import annotations


from core.campaign.story_generator import StoryGenerator, StoryArc


class TestStoryGeneratorInit:
    def test_create(self):
        gen = StoryGenerator()
        assert gen is not None


class TestStoryGeneratorRun:
    def test_generate_default(self):
        gen = StoryGenerator()
        arcs = gen.generate()
        assert len(arcs) >= 3
        for arc in arcs:
            assert isinstance(arc, StoryArc)

    def test_generate_issavi(self):
        gen = StoryGenerator()
        arcs = gen.generate(theme="Issavi")
        main_arcs = [a for a in arcs if a.is_main_story]
        assert len(main_arcs) >= 3

    def test_generate_with_level_range(self):
        gen = StoryGenerator()
        arcs = gen.generate(level_range=(200, 400))
        for arc in arcs:
            assert arc.required_level >= 200

    def test_generate_side_quests(self):
        gen = StoryGenerator()
        arcs = gen.generate(side_quests=True)
        side = [a for a in arcs if not a.is_main_story]
        assert len(side) >= 3

    def test_generate_no_side_quests(self):
        gen = StoryGenerator()
        arcs = gen.generate(side_quests=False)
        side = [a for a in arcs if not a.is_main_story]
        assert len(side) == 0

    def test_main_story_only(self):
        gen = StoryGenerator()
        arcs = gen.generate_main_story(theme="default")
        for arc in arcs:
            assert arc.is_main_story is True


class TestStoryArcData:
    def test_arc_has_objectives(self):
        gen = StoryGenerator()
        arcs = gen.generate()
        for arc in arcs:
            assert len(arc.objectives) > 0

    def test_arc_to_dict(self):
        arc = StoryArc(
            title="Test", chapter=1, description="Test desc", reward_gold=1000
        )
        d = arc.to_dict()
        assert d["title"] == "Test"
        assert d["chapter"] == 1
        assert d["reward_gold"] == 1000

    def test_arc_scaling(self):
        gen = StoryGenerator()
        low = gen.generate(level_range=(1, 50))
        high = gen.generate(level_range=(300, 500))
        # High level arcs should have higher required levels
        assert high[0].required_level >= low[0].required_level
