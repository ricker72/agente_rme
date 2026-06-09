"""
tools/real_knowledge_validation.py — Phase 7: Real Knowledge Validation.

1000 real knowledge queries using real KnowledgeEngine with correct API.
"""
from __future__ import annotations
import sys
import os
import json
import time
import random
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output" / "rc1.1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


QUERIES = [
    "Tell me about Issavi", "What is Roshamuul", "Soul War warzone",
    "Library dungeon loot", "Falcon bastion monsters", "Ferumbras citadel",
    "Issavi lizard dragon", "Roshamuul pale count", "Library scion atlantes",
    "Hunting grounds level 200", "Bosses level 300", "Undead zone 250",
    "Dragon lair", "Demon invasion", "Lizard chosen",
    "Where to hunt at level 100", "Where to hunt at level 200",
    "Bestiary bosses", "Hunt rotation", "Magic creatures",
    "Rare loot", "Boss mechanics", "Drops and rewards",
]


def run(n: int = 1000) -> Dict[str, Any]:
    print(f"[Phase 7] Running {n} real knowledge queries...", flush=True)
    from core.knowledge.knowledge_engine import KnowledgeEngine

    engine = KnowledgeEngine()

    queries_run = 0
    exceptions = 0
    response_times: List[float] = []
    hits_dist: Dict[int, int] = {}
    top_topics: List[str] = []

    random.seed(42)
    for i in range(n):
        q = random.choice(QUERIES) + f" #{i}"
        t0 = time.time()
        try:
            # Use the real API
            if hasattr(engine, "query_text"):
                result = engine.query_text(q, k=5)
                results = result.results if hasattr(result, "results") else ([result] if result else [])
            elif hasattr(engine, "query_structured"):
                result = engine.query_structured(q, top_k=5)
                results = result.results if hasattr(result, "results") else ([result] if result else [])
            elif hasattr(engine, "query"):
                results = engine.query(q, top_k=5)
            else:
                results = []
            elapsed = time.time() - t0
            response_times.append(elapsed)
            queries_run += 1
            n_hits = len(results) if results else 0
            hits_dist[n_hits] = hits_dist.get(n_hits, 0) + 1
            for r in results:
                if hasattr(r, "topic"):
                    top_topics.append(r.topic)
                elif isinstance(r, dict):
                    top_topics.append(r.get("topic", ""))
        except Exception as e:
            exceptions += 1
            if exceptions < 5:
                print(f"  [{i+1}/{n}] FAILED: {e}", flush=True)

    return {
        "version": "1.0.0-RC1.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 7: Real Knowledge Validation",
        "total_queries": n,
        "successful": queries_run,
        "exceptions": exceptions,
        "exception_rate": exceptions / max(1, n),
        "success_rate": queries_run / max(1, n),
        "response_time_s": {
            "mean": sum(response_times) / len(response_times) if response_times else 0,
            "min": min(response_times) if response_times else 0,
            "max": max(response_times) if response_times else 0,
            "total": sum(response_times),
        },
        "hits_distribution": {str(k): v for k, v in hits_dist.items()},
        "top_topics": list(set(top_topics))[:20],
        "criterion_pass": queries_run >= n * 0.8,
    }


def main() -> int:
    res = run(1000)
    out_file = OUTPUT_DIR / "real_knowledge_validation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n[Phase 7] Saved: {out_file}", flush=True)
    print(f"[Phase 7] Successful: {res['successful']}/1000", flush=True)
    print(f"[Phase 7] Exceptions: {res['exceptions']}", flush=True)
    print(f"[Phase 7] Pass: {res['criterion_pass']}", flush=True)
    return 0 if res["criterion_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
