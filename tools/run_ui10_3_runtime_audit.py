from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from tests.ui.runtime_audit_support import run_all_audits, write_runtime_reports

    results = run_all_audits()
    write_runtime_reports(results)
    print(results["final_status"])
    return 0 if results["final_status"] == "UI-10.3 RUNTIME AUDIT CERTIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
