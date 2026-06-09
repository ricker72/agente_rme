# Critic Report — soul_war_300

_Generated: 2026-06-08T15:14:21.723507  •  Version: 1.0_

## Overall Score: **61.7 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 48.0 |
| navigation | 85.0 |
| density | 42.5 |
| spawn | 58.0 |
| hunt | 50.0 |
| boss | 60.0 |
| city | 60.0 |
| decor | 74.5 |
| pathfinding | 84.4 |

## Issues (12)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | underdecorated_area | visual | - | Only 22% of ground tiles have content |
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,29,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (29,0,7) | Bottleneck: only 2 connections |
| warning | underdecorated_area | density | - | Only 15% of tiles have content |
| warning | spawn_cluster | spawn | (1,9) | Spawn cluster of 2 creatures at (1, 9) |
| warning | spawn_cluster | spawn | (2,18) | Spawn cluster of 2 creatures at (2, 18) |
| warning | spawn_cluster | spawn | (2,25) | Spawn cluster of 4 creatures at (2, 25) |
| warning | empty_region | region | hunt_soulwar | Region 'hunt_soulwar' is empty or near-empty (0 tiles) |
| warning | bottleneck | pathfinding | (29,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,29,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (7)

### Add visual content
_Priority: medium  •  Category: visual_

Large portions of the map are visually empty. Add items, spawns or decoration.

### Add decoration to empty areas
_Priority: medium  •  Category: density_

Large portions of the map are empty. Add decoration, structures or spawns to improve density.

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

Empty regions: hunt_soulwar. Add tiles, decoration or remove them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.
