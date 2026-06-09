# Critic Report — falcon_150

_Generated: 2026-06-08T15:14:21.923061  •  Version: 1.0_

## Overall Score: **68.7 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 68.4 |
| navigation | 85.0 |
| density | 58.9 |
| spawn | 67.0 |
| hunt | 50.0 |
| boss | 60.0 |
| city | 95.0 |
| decor | 82.5 |
| pathfinding | 84.2 |

## Issues (13)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,24,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (24,0,7) | Bottleneck: only 2 connections |
| warning | spawn_cluster | spawn | (0,5) | Spawn cluster of 4 creatures at (0, 5) |
| warning | spawn_cluster | spawn | (1,13) | Spawn cluster of 2 creatures at (1, 13) |
| warning | spawn_cluster | spawn | (2,2) | Spawn cluster of 2 creatures at (2, 2) |
| warning | empty_region | region | hunt_falcon | Region 'hunt_falcon' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_falcon | Region 'city_falcon' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_falcon_depot | Region 'city_falcon_depot' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_falcon_temple | Region 'city_falcon_temple' is empty or near-empty (0 tiles) |
| warning | bottleneck | pathfinding | (0,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (24,24,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (24,0,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (4)

### Spread spawn clusters
_Priority: low  •  Category: spawn_

Some spawns are clustered very close together. Spread them out for better gameplay.

### Define boss arenas
_Priority: low  •  Category: boss_

Add zones with names containing 'boss', 'arena', 'throne' or 'lair'.

### Populate empty regions
_Priority: medium  •  Category: region_

Empty regions: hunt_falcon, city_falcon, city_falcon_depot, city_falcon_temple. Add tiles, decoration or remove them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.
