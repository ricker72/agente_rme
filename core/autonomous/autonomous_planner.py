"""
Autonomous Planner - generates complete plans for world generation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .models.design_goal import DesignGoal
from .models.design_plan import DesignPlan
from .models.region_plan import RegionPlan
from .autonomous_director import AutonomousDirector


@dataclass
class AutonomousPlanner:
    """Generates complete plans for world generation."""
    
    director: AutonomousDirector = field(default_factory=AutonomousDirector)
    
    def create_plan(self, goal: DesignGoal) -> DesignPlan:
        """Create a complete plan based on the design goal."""
        plan_id = str(uuid.uuid4())
        
        # Get regions from director
        regions = self.director.decide_regions(goal)
        
        # Create plan
        plan = DesignPlan(
            plan_id=plan_id,
            goal_id=goal.prompt,  # Using prompt as goal ID
            description=f"Plan for: {goal.prompt}",
            regions=regions,
        )
        
        # Select blueprints and patterns for each region
        for region in plan.regions:
            region.blueprint_candidates = self.director.select_blueprints(region)
            region.patterns = self.director.select_patterns(region)
        
        # Calculate estimated complexity
        plan.estimated_complexity = self._calculate_complexity(plan)
        
        return plan
    
    def update_plan(self, plan: DesignPlan, feedback: Dict[str, Any]) -> DesignPlan:
        """Update a plan based on feedback."""
        # Adjust regions based on feedback
        if "add_region" in feedback:
            new_region = feedback["add_region"]
            plan.add_region(new_region)
        
        if "remove_region" in feedback:
            region_id = feedback["remove_region"]
            plan.regions = [r for r in plan.regions if r.region_id != region_id]
            plan.total_estimated_size = sum(r.target_size for r in plan.regions)
        
        if "modify_region" in feedback:
            region_id = feedback["modify_region"]["region_id"]
            modifications = feedback["modify_region"]["modifications"]
            for region in plan.regions:
                if region.region_id == region_id:
                    for key, value in modifications.items():
                        if hasattr(region, key):
                            setattr(region, key, value)
        
        # Recalculate complexity
        plan.estimated_complexity = self._calculate_complexity(plan)
        
        return plan
    
    def _calculate_complexity(self, plan: DesignPlan) -> float:
        """Calculate complexity score for the plan."""
        if not plan.regions:
            return 0.0
        
        complexity_factors = []
        
        # Number of regions
        region_count_factor = min(1.0, len(plan.regions) / 10.0)
        complexity_factors.append(region_count_factor)
        
        # Total size
        size_factor = min(1.0, plan.total_estimated_size / 10000.0)
        complexity_factors.append(size_factor)
        
        # Region type diversity
        region_types = set(r.region_type for r in plan.regions)
        diversity_factor = len(region_types) / 5.0  # 5 possible types
        complexity_factors.append(diversity_factor)
        
        # Average difficulty
        avg_difficulty = sum(r.target_difficulty for r in plan.regions) / len(plan.regions)
        complexity_factors.append(avg_difficulty)
        
        return sum(complexity_factors) / len(complexity_factors)
    
    def get_plan_summary(self, plan: DesignPlan) -> Dict[str, Any]:
        """Get a summary of the plan."""
        region_counts = {}
        for region in plan.regions:
            region_counts[region.region_type] = region_counts.get(region.region_type, 0) + 1
        
        return {
            "plan_id": plan.plan_id,
            "total_regions": len(plan.regions),
            "region_counts": region_counts,
            "total_estimated_size": plan.total_estimated_size,
            "estimated_complexity": plan.estimated_complexity,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "director": self.director.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutonomousPlanner":
        """Create from dictionary."""
        planner = cls()
        if "director" in data:
            planner.director = AutonomousDirector.from_dict(data["director"])
        return planner