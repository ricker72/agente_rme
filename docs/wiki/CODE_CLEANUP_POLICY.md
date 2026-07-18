# Code Cleanup Policy

## Keep

- A reachable import from a supported entry point.
- A package explicitly included by the active build manifest.
- Official-source parsers, certified material tables, OTBM roundtrip code, and current runtime resources.
- Abstract Planner knowledge with provenance and deterministic compilation.

## Remove

- Isolated modules with no runtime, build, CLI, or migration consumer.
- Placeholder systems that return fabricated success.
- Hard-coded item IDs not derived from official materials or exact item catalogs.
- Chat reports, obsolete plans, expired test artifacts, caches, and previous build products.

## Proof before deletion

Search entry points, imports, dynamic module loading, build manifests, migrations, and resource references. A similarly named replacement is not sufficient proof. On Windows, resolve every deletion target and verify it remains inside the intended project root.

## Build retention

Only the current build product is retained. A successful new build replaces the previous build atomically; failed builds do not delete the last known working product. Temporary tests and reports expire after 24 hours.

## GitHub size gate

No normal Git blob may reach 95 MiB. Derived databases, datasets, reference maps, official client assets, debug symbols, validation bundles, and compiled products remain local, are regenerated, or ship as Release assets. Run `scripts/github_size_guard.py` through repository hooks and CI before publishing.
