# Critic Report — roshamuul_400_600

_Generated: 2026-06-08T15:14:21.538040  •  Version: 1.0_

## Overall Score: **67.3 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 73.8 |
| navigation | 85.0 |
| density | 60.7 |
| spawn | 57.1 |
| hunt | 50.0 |
| boss | 60.0 |
| city | 60.0 |
| decor | 82.7 |
| pathfinding | 84.7 |

## Issues (10)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,39,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (39,0,7) | Bottleneck: only 2 connections |
| warning | spawn_cluster | spawn | (0,8) | Spawn cluster of 5 creatures at (0, 8) |
| warning | spawn_cluster | spawn | (0,24) | Spawn cluster of 3 creatures at (0, 24) |
| warning | spawn_cluster | spawn | (0,34) | Spawn cluster of 2 creatures at (0, 34) |
| warning | empty_region | region | hunt_roshamuul_main | Region 'hunt_roshamuul_main' is empty or near-empty (0 tiles) |
| warning | bottleneck | pathfinding | (0,39,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (39,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,0,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (5)

### Spread spawn clusters
_Priority: low  •  Category: spawn_

Some spawns are clustered very close together. Spread them out for better gameplay.

### Define boss arenas
_Priority: low  •  Category: boss_

Add zones with names containing 'boss', 'arena', 'throne' or 'lair'.

### Define city zones
_Priority: low  •  Category: city_

Add zones with names containing 'city', 'town', 'village', 'hub' or 'market'.

### Populate empty regions
_Priority: medium  •  Category: region_

Empty regions: hunt_roshamuul_main. Add tiles, decoration or remove them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.
