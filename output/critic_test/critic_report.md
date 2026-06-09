# Critic Report — test_issavi

_Generated: 2026-06-08T14:54:30.014502  •  Version: 1.0_

## Overall Score: **53.3 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 45.6 |
| navigation | 85.0 |
| density | 55.5 |
| spawn | 22.5 |
| hunt | 50.0 |
| boss | 40.0 |
| city | 45.0 |
| decor | 67.8 |
| pathfinding | 83.8 |

## Issues (14)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,19,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (19,0,7) | Bottleneck: only 2 connections |
| warning | low_spawn_density | spawn | - | Spawn density 1.25% is below target 5% |
| warning | spawn_cluster | spawn | (5,5) | Spawn cluster of 5 creatures at (5, 5) |
| error | boss_no_escape | boss | boss_arena | Boss arena 'boss_arena' has no escape route |
| error | city_missing_services | city | city_issavi_depot | City 'city_issavi_depot' is missing required service: depot |
| error | city_missing_services | city | city_issavi_temple | City 'city_issavi_temple' is missing required service: temple |
| warning | empty_region | region | city_issavi | Region 'city_issavi' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_issavi_depot | Region 'city_issavi_depot' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_issavi_temple | Region 'city_issavi_temple' is empty or near-empty (0 tiles) |
| warning | bottleneck | pathfinding | (19,19,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,19,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (7)

### Increase spawn density
_Priority: medium  •  Category: spawn_

Add more monster spawns in hunt areas to reach the target density.

### Spread spawn clusters
_Priority: low  •  Category: spawn_

Some spawns are clustered very close together. Spread them out for better gameplay.

### Add escape route to boss_arena
_Priority: high  •  Category: boss_
_Location: boss_arena_

Boss arena 'boss_arena' has no escape route. Add a secondary exit or teleport.

### Add depot to city_issavi_depot
_Priority: high  •  Category: city_
_Location: city_issavi_depot_

City 'city_issavi_depot' has no depot zone. Add a zone named like 'city_city_issavi_depot_depot'.

### Add temple to city_issavi_temple
_Priority: high  •  Category: city_
_Location: city_issavi_temple_

City 'city_issavi_temple' has no temple zone. Add a zone named like 'city_city_issavi_temple_temple'.

### Populate empty regions
_Priority: medium  •  Category: region_

Empty regions: city_issavi, city_issavi_depot, city_issavi_temple. Add tiles, decoration or remove them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.
