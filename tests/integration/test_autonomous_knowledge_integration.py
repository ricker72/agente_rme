"""Integration test: Autonomous Designer + Knowledge Engine."""

import pytest

from core.autonomous import AutonomousWorldDesigner
from core.autonomous.autonomous_decision_engine import AutonomousDecisionEngine
from core.autonomous.models.region_plan import RegionPlan


class _MockKnowledgeEngine:
    def __init__(self):
        self.calls = []

    def find_similar_hunts(self, name, k=5):
        self.calls.append(("hunt", name))
        return [{"name": f"pattern_{name}_a"}, {"name": f"pattern_{name}_b"}]

    def find_similar_cities(self, name, k=5):
        self.calls.append(("city", name))
        return [{"name": f"city_pattern_{name}"}]

    def find_similar_boss_rooms(self, name, k=5):
        return []

    def find_similar_raids(self, name, k=5):
        return []

    def find_similar_regions(self, name, k=5):
        return []


def test_decision_engine_uses_knowledge_engine():
    ke = _MockKnowledgeEngine()
    engine = AutonomousDecisionEngine(knowledge_engine=ke)
    region = RegionPlan(region_id="r1", region_name="Hunt", region_type="hunt")
    decision = engine.select_pattern(region)
    assert "pattern_Hunt_a" in [decision.selected_option] + decision.alternatives
    assert any(call[0] == "hunt" for call in ke.calls)


def test_director_uses_knowledge_engine():
    ke = _MockKnowledgeEngine()
    designer = AutonomousWorldDesigner(output_dir="output/test_designer_ke")
    designer.wire_subsystems(knowledge_engine=ke)
    designer.optimizer.max_iterations = 1
    designer.optimizer.use_real_engines = False
    designer.generate("Hunt 200", max_iterations=1)
    # At least one find_similar_* should have been called
    assert any(c[0] in ("hunt", "city", "boss", "raid", "region") for c in ke.calls)
