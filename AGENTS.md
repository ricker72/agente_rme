# Mandatory RME/OpenTibia preflight

Before inspecting, planning, editing, testing, building, packaging, deleting, or migrating code in this repository, invoke the `rme-opentibia-code-guardian` skill and follow it as a blocking gate.

Read `docs/wiki/README.md`, `docs/wiki/AI_CODE_GUARDIAN.md`, and the relevant wiki pages. Then inspect the current Canary/RME source and official material/OTB/appearance data that own the requested behavior. State the exact evidence files before editing.

Do not invent OpenTibia IDs, flags, materials, brushes, borders, OTBM behavior, renderer rules, or successful results. Do not add placeholder production code, duplicate engines, direct AI-to-tile writes, or speculative compatibility code. If authoritative evidence cannot be found, stop and report the missing specification.

Workspace changes must preserve the shared certified engine boundary. Reference maps provide abstract style evidence only; never copy their geometry.

Before committing or pushing, run `python scripts/github_size_guard.py --tracked --history`. Never add a normal Git blob of 95 MiB or more. Generated datasets, Planner databases, maps, official assets, debug symbols, bundles, and builds belong in local storage, deterministic regeneration, Git LFS by explicit decision, or GitHub Releases.

Run `python scripts/secret_guard.py --tracked --history` before publication. API credentials, tokens, private keys, or user-specific connection secrets must never exist in source, configuration defaults, logs, builds, databases, or Git history. Runtime integrations may read named environment variables or an operating-system secret store only.
