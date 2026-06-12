# UI Change Policy: release/ui-v1

## Snapshot Metadata

```json
{
  "status": "FROZEN",
  "release": "ui-v1.0",
  "support": "SUPPORTED"
}
```

## Purpose

`release/ui-v1` is the supported production branch for Agente RME Studio UI v1.0. It is frozen for production support and certification preservation.

## Allowed Changes

Only the following changes are allowed on `release/ui-v1`:

- Bug fixes
- Crash fixes
- Memory leak fixes
- Security fixes
- UI-10 certification fixes

Every change must preserve the certified UI architecture, pass the UI quality gates, and avoid frozen-core modifications.

## Forbidden Changes

The following changes are forbidden on `release/ui-v1`:

- New widgets
- New pages
- New adapters
- Redesigns
- Architecture changes
- Feature development

## Feature Work Policy

All future feature work must be developed outside `release/ui-v1` on one of these branch families:

- `develop`
- `feature/*`
- `release/v1.1`

## Required Gates For release/ui-v1 Fixes

Before any support fix is accepted, run:

```powershell
python -m ruff check ui tests/ui
python -m flake8 ui tests/ui
python -m mypy ui tests/ui
python -m pytest tests/ui -v
```

Certification-impacting fixes must also update the relevant `baseline/ui-freeze/` or `baseline/ui-production/` evidence files.
