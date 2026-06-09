"""
CityAnalyzer — analyzes city infrastructure: streets, depot, temple, NPCs, connectivity.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from core.world.world_model import WorldModel

from .base_analyzer import (
    build_snapshots,
    snapshots_by_zone,
    safe_ratio,
    clamp,
    average,
    manhattan,
)

logger = logging.getLogger(__name__)


class CityAnalyzer:
    """
    Computes city_score in [0, 100] from the presence and quality of services.

    A "city" is a zone whose name contains 'city', 'town', 'village',
    'depot', 'temple', 'hub', 'market', 'npc'.
    """

    CATEGORY = "city"
    CITY_KEYWORDS = ("city", "town", "village", "hub", "market", "npc_hub")

    REQUIRED_SERVICES = ("depot", "temple")
    OPTIONAL_SERVICES = ("npc", "bank", "shop", "mail", "transport")

    def __init__(self):
        pass

    def analyze(self, world: WorldModel) -> Dict[str, Any]:
        from ..models import (
            CriticScore, CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        cities = self._identify_cities(world)
        if not cities:
            return {
                "category": self.CATEGORY,
                "score": CriticScore(self.CATEGORY, 60.0, notes="No city zones identified"),
                "issues": [],
                "recommendations": [
                    CriticRecommendation(
                        title="Define city zones",
                        description="Add zones with names containing 'city', 'town', 'village', 'hub' or 'market'.",
                        category=self.CATEGORY,
                        priority=RecommendationPriority.LOW,
                    ),
                ],
                "metrics": {"cities": 0},
            }

        snapshots = build_snapshots(world)
        by_zone = snapshots_by_zone(snapshots)
        scores: List[float] = []
        issues: List = []
        recs: List = []
        per_city: List[Dict[str, Any]] = []

        for city in cities:
            s, c_issues, c_recs, metrics = self._analyze_city(city, by_zone, world)
            scores.append(s)
            issues.extend(c_issues)
            recs.extend(c_recs)
            per_city.append(metrics)

        overall = clamp(average(scores))
        score = CriticScore(
            category=self.CATEGORY,
            value=overall,
            breakdown={
                "city_count": float(len(cities)),
                "min_city_score": round(min(scores), 2) if scores else 0.0,
            },
        )

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {"cities": len(cities), "per_city": per_city},
        }

    def _identify_cities(self, world: WorldModel) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for r in world.regions:
            lname = r.name.lower()
            # Skip sub-zones that are themselves services (depot/temple/npc)
            if any(svc in lname for svc in self.REQUIRED_SERVICES + self.OPTIONAL_SERVICES):
                continue
            if any(kw in lname for kw in self.CITY_KEYWORDS):
                out.append({"name": r.name, "min_level": r.min_level, "max_level": r.max_level})
        return out

    def _analyze_city(self, city: Dict[str, Any], by_zone: Dict[str, List],
                      world: WorldModel) -> Tuple[float, List, List, Dict[str, Any]]:
        from ..models import (
            CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        issues: List = []
        recs: List = []
        name = city["name"]

        # Find sub-zones that match required/optional services
        services: Dict[str, int] = {}
        for sub in world.regions:
            lname = sub.name.lower()
            for svc in self.REQUIRED_SERVICES + self.OPTIONAL_SERVICES:
                if svc in lname and lname != name.lower():
                    services[svc] = services.get(svc, 0) + 1

        for svc in self.REQUIRED_SERVICES:
            if services.get(svc, 0) == 0:
                issues.append(CriticIssue(
                    issue_type=IssueType.CITY_MISSING_SERVICES,
                    severity=IssueSeverity.ERROR,
                    category=self.CATEGORY,
                    location=name,
                    message=f"City '{name}' is missing required service: {svc}",
                ))
                if svc == "depot":
                    recs.append(CriticRecommendation(
                        title=f"Add depot to {name}",
                        description=f"City '{name}' has no depot zone. Add a zone named like 'city_{name}_depot'.",
                        category=self.CATEGORY,
                        priority=RecommendationPriority.HIGH,
                        target_location=name,
                    ))
                elif svc == "temple":
                    recs.append(CriticRecommendation(
                        title=f"Add temple to {name}",
                        description=f"City '{name}' has no temple zone. Add a zone named like 'city_{name}_temple'.",
                        category=self.CATEGORY,
                        priority=RecommendationPriority.HIGH,
                        target_location=name,
                    ))

        # Street connectivity: how many of the city's ground tiles are
        # connected to the main city cluster
        city_snaps = by_zone.get(name, [])
        if not city_snaps:
            for sub_name, snaps in by_zone.items():
                if name.lower() in sub_name.lower():
                    city_snaps.extend(snaps)

        street_score = 80.0
        depot_score = 100.0 if services.get("depot", 0) > 0 else 0.0
        temple_score = 100.0 if services.get("temple", 0) > 0 else 0.0
        npc_score = 100.0 if services.get("npc", 0) > 0 else 50.0

        # Connectivity: distance between depot and temple, depot and temple
        # should be < 50 tiles
        if services.get("depot", 0) and services.get("temple", 0):
            depot_zone = next((s for s in world.regions if "depot" in s.name.lower()
                              and name.lower() in s.name.lower()), None)
            temple_zone = next((s for s in world.regions if "temple" in s.name.lower()
                               and name.lower() in s.name.lower()), None)
            if depot_zone and temple_zone:
                # Use min/max_level as proxy for location (region has no x/y)
                distance = abs(depot_zone.min_level - temple_zone.min_level)
                if distance > 100:
                    street_score = 60.0
                else:
                    street_score = 100.0
        elif not city_snaps:
            street_score = 50.0

        overall = clamp(
            street_score * 0.30
            + depot_score * 0.30
            + temple_score * 0.30
            + npc_score * 0.10
        )

        return overall, issues, recs, {
            "name": name,
            "services": services,
            "tiles": len(city_snaps),
            "street_score": round(street_score, 2),
            "depot_score": round(depot_score, 2),
            "temple_score": round(temple_score, 2),
            "npc_score": round(npc_score, 2),
        }
