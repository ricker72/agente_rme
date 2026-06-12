"""Integration test: Autonomous Designer + Blueprint Intelligence."""

from core.autonomous import AutonomousWorldDesigner
from core.autonomous.autonomous_decision_engine import AutonomousDecisionEngine
from core.autonomous.models.region_plan import RegionPlan


class _MockBlueprintIntelligence:
    def __init__(self):
        self.calls = []

    def recommend(self, region_type, top_k=5):
        self.calls.append(region_type)
        return [
            {"name": f"smart_{region_type}_bp_1"},
            {"name": f"smart_{region_type}_bp_2"},
        ]


def test_decision_engine_uses_blueprint_intelligence():
    bi = _MockBlueprintIntelligence()
    engine = AutonomousDecisionEngine(blueprint_intelligence=bi)
    region = RegionPlan(region_id="r1", region_name="Hunt", region_type="hunt")
    decision = engine.select_blueprint(region)
    assert "smart_hunt_bp_1" in [decision.selected_option] + decision.alternatives
    assert bi.calls == ["hunt"]


def test_director_uses_blueprint_intelligence():
    bi = _MockBlueprintIntelligence()
    designer = AutonomousWorldDesigner(output_dir="output/test_designer_bp")
    designer.wire_subsystems(blueprint_intelligence=bi)
    designer.optimizer.max_iterations = 1
    designer.optimizer.use_real_engines = False
    designer.generate("Hunt 200", max_iterations=1)
    assert "hunt" in bi.calls
