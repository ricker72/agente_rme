"""
Critic analyzers — modular, pluggable analyzers that each contribute a score.
"""

from .base_analyzer import (
    TileSnapshot,
    Region,
    build_snapshots,
    snapshots_by_zone,
    snapshots_by_z,
    find_regions,
    manhattan,
    euclidean,
    safe_ratio,
    clamp,
    average,
    percentile,
    stddev,
    histogram,
)
from .pathfinding_analyzer import (
    PathfindingAnalyzer,
    WalkableGraph,
    bfs,
    dijkstra,
    astar,
    octile_heuristic,
    manhattan_heuristic,
    octile_cost,
)
from .navigation_analyzer import NavigationAnalyzer
from .density_analyzer import DensityAnalyzer
from .spawn_analyzer import SpawnAnalyzer
from .hunt_analyzer import HuntAnalyzer
from .boss_room_analyzer import BossRoomAnalyzer
from .city_analyzer import CityAnalyzer
from .decor_analyzer import DecorAnalyzer
from .region_analyzer import RegionAnalyzer
from .visual_analyzer import VisualAnalyzer

__all__ = [
    "TileSnapshot",
    "Region",
    "build_snapshots",
    "snapshots_by_zone",
    "snapshots_by_z",
    "find_regions",
    "manhattan",
    "euclidean",
    "safe_ratio",
    "clamp",
    "average",
    "percentile",
    "stddev",
    "histogram",
    "PathfindingAnalyzer",
    "WalkableGraph",
    "bfs",
    "dijkstra",
    "astar",
    "octile_heuristic",
    "manhattan_heuristic",
    "octile_cost",
    "NavigationAnalyzer",
    "DensityAnalyzer",
    "SpawnAnalyzer",
    "HuntAnalyzer",
    "BossRoomAnalyzer",
    "CityAnalyzer",
    "DecorAnalyzer",
    "RegionAnalyzer",
    "VisualAnalyzer",
]
