---
name: rme-opentibia-code-guardian
description: Mandatory preflight for all coding, debugging, testing, building, packaging, cleanup, map, renderer, brush, Planner, AI, database, Workspace, and OTBM work in Agente RME AI. Requires wiki and current Canary/RME/OpenTibia evidence before edits and prohibits invented game data or vibe coding.
---

# RME OpenTibia Code Guardian

Read `/AGENTS.md` and `/docs/wiki/AI_CODE_GUARDIAN.md`. Run the installed `rme-opentibia-code-guardian` preflight when available. Inspect and cite the current source or official data that owns the behavior, trace the active runtime consumer, then implement through certified shared services. Stop when evidence is missing. Validate the real entry point and never invent IDs, flags, materials, brushes, OTBM rules, renderer behavior, or passing results.

Before commit or push, run `python scripts/github_size_guard.py --tracked --history`. Normal Git blobs must remain below 95 MiB; large generated or binary artifacts belong in local regeneration, GitHub Releases, or deliberately configured Git LFS.

Also run `python scripts/secret_guard.py --tracked --history`. Credentials may be obtained only from environment variables or an operating-system secret store and must never appear in source, logs, databases, builds, or Git history.
