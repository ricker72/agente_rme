# Critic Report — darashia_150

_Generated: 2026-06-08T15:14:22.010625  •  Version: 1.0_

## Overall Score: **67.4 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 67.5 |
| navigation | 85.0 |
| density | 59.0 |
| spawn | 57.5 |
| hunt | 50.0 |
| boss | 60.0 |
| city | 95.0 |
| decor | 83.3 |
| pathfinding | 83.8 |

## Issues (11)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,19,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (19,0,7) | Bottleneck: only 2 connections |
| warning | low_spawn_density | spawn | - | Spawn density 1.25% is below target 5% |
| warning | empty_region | region | city_darashia | Region 'city_darashia' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_darashia_depot | Region 'city_darashia_depot' is empty or near-empty (0 tiles) |
| warning | empty_region | region | city_darashia_temple | Region 'city_darashia_temple' is empty or near-empty (0 tiles) |
| warning | empty_region | region | hunt_darashia | Region 'hunt_darashia' is empty or near-empty (0 tiles) |
| warning | bottleneck | pathfinding | (19,19,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,19,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (4)

### Increase spawn density
_Priority: medium  •  Category: spawn_

Add more monster spawns in hunt areas to reach the target density.

### Define boss arenas
_Priority: low  •  Category: boss_

Add zones with names containing 'boss', 'arena', 'throne' or 'lair'.

### Populate empty regions
_Priority: medium  •  Category: region_

Empty regions: city_darashia, city_darashia_depot, city_darashia_temple, hunt_darashia. Add tiles, decoration or remove them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.
