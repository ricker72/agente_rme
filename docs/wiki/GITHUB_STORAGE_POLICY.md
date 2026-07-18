# GitHub Storage Policy

The source repository must remain cloneable without GitHub large-file rejection.

## Hard gate

- Keep every normal Git blob below 95 MiB, leaving margin below GitHub's 100 MiB limit.
- Run `python scripts/github_size_guard.py --tracked --history` before publishing.
- Use the repository hooks through `git config core.hooksPath .githooks`.
- CI repeats the full tracked-file and history check on every push and pull request.

## Storage classes

- Commit source code, schemas, compact configuration, migrations, wiki pages, and small deterministic fixtures.
- Regenerate caches, reports, compiled binaries, PDB/ILK files, Planner working databases, and derived datasets locally.
- Distribute versioned application builds and validation bundles as GitHub Release assets.
- Use Git LFS only for a deliberately versioned binary that cannot be regenerated or delivered as a Release.
- Keep official client assets and large reference maps outside normal Git. Resolve them through first-run configuration or documented local paths.

Compressing a large generated file into the source tree is not a substitute for proper storage ownership. A compressed seed may be committed only when the runtime has a verified deterministic unpack/migration path and the resulting Git blob remains below 95 MiB.

## Build retention

A successful build atomically replaces the previous build product. Failed builds retain the last known working product. Old builds, temporary reports, and test artifacts must not enter Git.
