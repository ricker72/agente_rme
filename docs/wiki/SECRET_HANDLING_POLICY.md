# Secret Handling Policy

## Prohibited storage

API credentials, bearer tokens, private keys, and user-specific connection secrets must not be committed, embedded in application binaries, written to logs, stored in Planner databases, or added to generated reports. This applies to Agente RME AI and RME Workspace.

## Runtime configuration

Provider integrations may read a credential from an environment variable or an operating-system secret store. Source code may contain the environment variable name, but never a default credential value. Diagnostic output may report only whether a provider is configured.

## Publication gate

Run `python scripts/secret_guard.py --tracked --history` before commit or push. The repository hooks and GitHub workflow execute the same deterministic scan and hide matched values from their output.

When a credential is detected:

1. Remove it from the working tree and Git history.
2. Revoke or rotate it at the provider.
3. Clear generated builds, logs, caches, and databases that may contain it.
4. Repeat the full tree and history scan before publication.
