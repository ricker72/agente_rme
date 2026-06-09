"""Replace datetime.utcnow() with datetime.now(timezone.utc) in project files."""
import os
import re

# (file_path, original_import_block, replacement_import_block) — only modify the
# files that actually use utcnow().
TARGETS = [
    # agent_result.py — uses `from datetime import datetime`
    (
        "agente_rme/core/agents/agent_result.py",
        "from datetime import datetime",
        "from datetime import datetime, timezone",
    ),
    # agent_response.py — uses `import datetime` and `datetime.datetime.utcnow()`
    (
        "agente_rme/core/agents/contracts/agent_response.py",
        "import datetime",
        "import datetime\nfrom datetime import timezone",
    ),
    # agent_task.py — uses `from datetime import datetime`
    (
        "agente_rme/core/agents/contracts/agent_task.py",
        "from datetime import datetime",
        "from datetime import datetime, timezone",
    ),
    # workflow_state.py — uses `from datetime import datetime`
    (
        "agente_rme/core/agents/contracts/workflow_state.py",
        "from datetime import datetime",
        "from datetime import datetime, timezone",
    ),
    # orchestrator_agent.py — uses `import datetime` and `datetime.datetime.utcnow()`
    (
        "agente_rme/core/agents/orchestrator_agent.py",
        "import datetime",
        "import datetime\nfrom datetime import timezone",
    ),
    # report_generator.py — uses `from datetime import datetime`
    (
        "agente_rme/core/playtest/report_generator.py",
        "from datetime import datetime",
        "from datetime import datetime, timezone",
    ),
]

ROOT = os.path.dirname(os.path.abspath(__file__))

count = 0
for rel_path, orig_import, new_import in TARGETS:
    abs_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(abs_path):
        print(f"MISSING: {rel_path}")
        continue
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    # Replace the import block (only the first occurrence)
    if orig_import in content and "from datetime import timezone" not in content:
        content = content.replace(orig_import, new_import, 1)

    # Replace utcnow calls
    # 1) `datetime.utcnow()` -> `datetime.now(timezone.utc)`
    content = re.sub(r"\bdatetime\.utcnow\(\)", "datetime.now(timezone.utc)", content)
    # 2) `datetime.datetime.utcnow()` -> `datetime.datetime.now(datetime.timezone.utc)`
    content = re.sub(
        r"\bdatetime\.datetime\.utcnow\(\)",
        "datetime.datetime.now(datetime.timezone.utc)",
        content,
    )

    if content != original:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1
        print(f"FIXED: {rel_path}")
    else:
        print(f"NO-CHANGE: {rel_path}")

print(f"\nTotal files fixed: {count}")
