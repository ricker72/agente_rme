# Critic Report — library_200

_Generated: 2026-06-08T15:14:21.827241  •  Version: 1.0_

## Overall Score: **69.5 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 80.2 |
| navigation | 85.0 |
| density | 77.4 |
| spawn | 44.0 |
| hunt | 50.0 |
| boss | 60.0 |
| city | 60.0 |
| decor | 98.6 |
| pathfinding | 83.8 |

## Issues (9)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,19,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (19,0,7) | Bottleneck: only 2 connections |
| warning | spawn_cluster | spawn | (2,13) | Spawn cluster of 3 creatures at (2, 13) |
| warning | spawn_cluster | spawn | (12,11) | Spawn cluster of 3 creatures at (12, 11) |
| warning | empty_region | region | library | Region 'library' is empty or near-empty (0 tiles) |
| warning | bottleneck | pathfinding | (19,19,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,19,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (6)

### Spread spawn clusters
_Priority: low  •  Category: spawn_

Some spawns are clustered very close together. Spread them out for better gameplay.

### Define hunt zones
_Priority: low  •  Category: hunt_

Add zones with names containing 'hunt', 'spawn', 'farm' or 'cave' to enable hunt analysis.

### Define boss arenas
_Priority: low  •  Category: boss_

Add zones with names containing 'boss', 'arena', 'throne' or 'lair'.

### Define city zones
_Priority: low  •  Category: city_

Add zones with names containing 'city', 'town', 'village', 'hub' or 'market'.

### Populate empty regions
_Priority: medium  •  Category: region_

Empty regions: library. Add tiles, decoration or remove them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.
