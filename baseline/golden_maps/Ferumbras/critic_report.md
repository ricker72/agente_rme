# Critic Report — ancient_temple_300

_Generated: 2026-06-08T15:14:22.180597  •  Version: 1.0_

## Overall Score: **67.2 / 100**

### Per-category scores

| Category | Score |
|----------|-------|
| visual | 80.8 |
| navigation | 85.0 |
| density | 73.1 |
| spawn | 31.1 |
| hunt | 50.0 |
| boss | 60.0 |
| city | 60.0 |
| decor | 95.3 |
| pathfinding | 84.6 |

## Issues (8)

| Severity | Type | Category | Location | Message |
|----------|------|----------|----------|---------|
| warning | bottleneck | navigation | (0,0,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (0,34,7) | Bottleneck: only 2 connections |
| warning | bottleneck | navigation | (34,0,7) | Bottleneck: only 2 connections |
| warning | low_spawn_density | spawn | - | Spawn density 0.41% is below target 5% |
| warning | empty_region | region | ancient_temple | Region 'ancient_temple' is empty or near-empty (0 tiles) |
| warning | bottleneck | pathfinding | (0,0,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (34,34,7) | Navigation bottleneck detected — routes funnel through this tile |
| warning | bottleneck | pathfinding | (0,34,7) | Navigation bottleneck detected — routes funnel through this tile |

## Recommendations (6)

### Increase spawn density
_Priority: medium  •  Category: spawn_

Add more monster spawns in hunt areas to reach the target density.

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

Empty regions: ancient_temple. Add tiles, decoration or remove them.

### Reduce navigation bottlenecks
_Priority: medium  •  Category: pathfinding_

Add secondary routes around bottleneck tiles to improve movement.
