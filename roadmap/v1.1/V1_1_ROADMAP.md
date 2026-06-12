# Agente RME v1.1 Roadmap

## Snapshot Metadata

```json
{
  "status": "FROZEN",
  "release": "ui-v1.0",
  "support": "SUPPORTED"
}
```

## Release Objective

Agente RME v1.1 starts from the certified UI v1.0 production baseline and focuses development on real map-generation intelligence, deeper critic evaluation, and iterative autonomous improvement.

## Primary Themes

- World Generator 2.0
- Blueprint Intelligence 2.0
- Visual Critic 2.0
- Autonomous Designer 2.0

## World Generator 2.0

Deliver real generation workflows for:

- Cities
- Hunts
- Dungeons
- Boss Areas
- Quest Chains

## Blueprint Intelligence 2.0

Learn production-grade patterns from canonical Tibia-like references:

- Issavi
- Roshamuul
- Soul War
- Falcon Bastion
- Library
- Ferumbras

## Visual Critic 2.0

Evaluate generated content across:

- Pathing
- Density
- Spawn Quality
- Progression
- Reward Loops

## Autonomous Designer 2.0

Support an iterative design loop:

Generate -> Critic -> Improve -> Critic -> Improve

The loop should continue until the target score is reached or a configured iteration limit stops the workflow.

## Branching

Feature development belongs on `develop`, `feature/*`, or `release/v1.1`. The `release/ui-v1` branch remains frozen for production support only.
