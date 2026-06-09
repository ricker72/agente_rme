# Critic Report — venore_80

_Generated: 2026-06-08T15:14:22.391718  •  Version: 1.0_

## Overall Score: **68.5 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 66.4 |
| navigation | 85.0 |
| density | 55.1 |
| spawn | 56.9 |
| hunt | 50.0 |
| boss | 80.0 |
| city | 95.0 |
| decor | 79.7 |
| pathfinding | 84.4 |

## Issues (13)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,29,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (29,0,7) | Bottleneck: only 2 connections |
| warning | spawn_cluster | spawn | (3,19) | Spawn cluster of 2 creatures at (3, 19) |
| warning | spawn_cluster | spawn | (3,26) | Spawn cluster of 2 creatures at (3, 26) |
| warning | spawn_cluster | spawn | (4,1) | Spawn cluster of 2 creatures at (4, 1) |
| warning | empty_region | region | city_venore | Region 'city_venore' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_venore_depot | Region 'city_venore_depot' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_venore_temple | Region 'city_venore_temple' is empty or near-empty (0 tiles) |
| warning | empty_region | region | hunt_venore | Region 'hunt_venore' is empty or near-empty (0 tiles) |
| warning | bottleneck | pathfinding | (29,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,29,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (3)

### Spread spawn clusters
_Priority: low  •  Category: spawn_

Some spawns are clustered very close together. Spread them out for better gameplay.

### Populate empty regions
_Priority: medium  •  Category: region_

Empty regions: city_venore, city_venore_depot, city_venore_temple, hunt_venore. Add tiles, decoration or remove them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.
