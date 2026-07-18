"""Configure encrypted AI-provider credentials without command-line key arguments."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.ai.secret_store import AISecretStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Agente RME AI credentials with Windows DPAPI")
    parser.add_argument("action", choices=("set", "delete", "status"))
    parser.add_argument("provider", choices=("paxsenix", "openrouter", "custom", "ollama"))
    args = parser.parse_args()
    store = AISecretStore()
    if args.action == "status":
        print(f"{args.provider}: {'CONFIGURED' if store.configured(args.provider) else 'NOT_CONFIGURED'}")
        return 0
    if args.action == "delete":
        store.delete(args.provider)
        print(f"{args.provider}: DELETED")
        return 0
    first = getpass.getpass(f"New {args.provider} API key: ")
    second = getpass.getpass("Confirm API key: ")
    if first != second:
        print("Keys do not match", file=sys.stderr)
        return 2
    store.set(args.provider, first)
    print(f"{args.provider}: CONFIGURED_WITH_WINDOWS_DPAPI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
