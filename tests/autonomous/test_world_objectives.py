"""Tests for World Objectives."""

import pytest

from core.autonomous.world_objective import WorldObjective, ObjectiveType


class TestWorldObjective:
    """Test cases for WorldObjective."""

    def test_create_quality_objective(self):
        obj = WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=0.9)
        assert obj.objective_type == ObjectiveType.QUALITY
        assert obj.weight == 1.0

    def test_invalid_weight_raises(self):
        with pytest.raises(ValueError):
            WorldObjective(objective_type=ObjectiveType.QUALITY, weight=1.5)

    def test_invalid_target_raises(self):
        with pytest.raises(ValueError):
            WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=1.5)

    def test_evaluate_below_target(self):
        obj = WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=0.8, weight=1.0)
        score = obj.evaluate(0.4)
        # 0.4 / 0.8 = 0.5, weight 1.0 → 0.5
        assert score == pytest.approx(0.5)

    def test_evaluate_at_target(self):
        obj = WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=0.8, weight=1.0)
        score = obj.evaluate(0.9)
        assert score == 1.0

    def test_evaluate_above_target_caps_at_one(self):
        obj = WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=0.5, weight=1.0)
        score = obj.evaluate(1.0)
        assert score == 1.0

    def test_threshold_penalty(self):
        obj = WorldObjective(
            objective_type=ObjectiveType.QUALITY, target_value=0.9,
            threshold=0.5, weight=1.0,
        )
        score = obj.evaluate(0.4)  # below threshold → 0.5 penalty
        assert score < 0.5

    def test_get_status_achieved(self):
        obj = WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=0.5)
        obj.evaluate(0.6)
        assert obj.get_status() == "achieved"

    def test_get_status_in_progress(self):
        obj = WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=0.9, threshold=0.5)
        obj.evaluate(0.6)
        assert obj.get_status() == "in_progress"

    def test_get_status_not_started(self):
        obj = WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=0.9, threshold=0.5)
        obj.evaluate(0.2)
        assert obj.get_status() == "not_started"

    def test_to_dict_from_dict(self):
        obj = WorldObjective(objective_type=ObjectiveType.QUALITY, target_value=0.9, weight=0.5)
        data = obj.to_dict()
        assert data["objective_type"] == "quality"
        assert data["target_value"] == 0.9
        restored = WorldObjective.from_dict(data)
        assert restored.objective_type == ObjectiveType.QUALITY

    def test_all_objective_types(self):
        for t in (
            ObjectiveType.QUALITY, ObjectiveType.DENSITY, ObjectiveType.NAVIGATION,
            ObjectiveType.BOSS, ObjectiveType.CITY, ObjectiveType.DIFFICULTY,
            ObjectiveType.PLAYTEST, ObjectiveType.CRITIC, ObjectiveType.REUSE,
        ):
            obj = WorldObjective(objective_type=t, target_value=0.5)
            assert obj.objective_type == t
