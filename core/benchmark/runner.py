from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional
import tracemalloc


@dataclass
class BenchmarkResult:
    name: str = ""
    duration_ms: float = 0.0
    memory_kb: float = 0.0
    tiles_generated: int = 0
    tiles_per_second: float = 0.0
    export_duration_ms: float = 0.0
    total_iterations: int = 1


class BenchmarkRunner:
    """Measures generation performance: time, memory, tiles/sec."""

    def __init__(self, iterations: int = 1):
        self.iterations = iterations
        self._results: List[BenchmarkResult] = []
        self._start_time: float = 0.0
        self._start_memory: float = 0.0
        self._is_tracking = False
        self._track_name = ""

    def start(self, name: str) -> None:
        self._track_name = name
        self._start_time = time.perf_counter()
        if tracemalloc.is_tracing():
            self._start_memory = tracemalloc.get_traced_memory()[0] / 1024
        self._is_tracking = True

    def stop(self, tiles: int = 0, export_ms: float = 0.0) -> BenchmarkResult:
        duration_ms = (time.perf_counter() - self._start_time) * 1000
        mem_used = 0.0
        if tracemalloc.is_tracing():
            mem_used = max(0, tracemalloc.get_traced_memory()[0] / 1024 - self._start_memory)
        tps = tiles / (duration_ms / 1000) if duration_ms > 0 else 0
        result = BenchmarkResult(
            name=self._track_name, duration_ms=duration_ms,
            memory_kb=mem_used, tiles_generated=tiles,
            tiles_per_second=tps, export_duration_ms=export_ms,
            total_iterations=self.iterations,
        )
        self._results.append(result)
        self._is_tracking = False
        return result

    def run_benchmark(self, fn, name: str, tiles_expected: int = 0, **kwargs):
        """Run multiple iterations and return averaged result."""
        durations, memories = [], []
        for _ in range(self.iterations):
            self.start(name)
            result = fn(**kwargs)
            tiles = tiles_expected or len(getattr(result, "tiles", []))
            r = self.stop(tiles=tiles)
            durations.append(r.duration_ms)
            memories.append(r.memory_kb)
        avg = lambda xs: sum(xs) / len(xs) if xs else 0
        return BenchmarkResult(
            name=name, duration_ms=avg(durations),
            memory_kb=avg(memories), tiles_generated=tiles_expected,
            tiles_per_second=tiles_expected / (avg(durations) / 1000) if avg(durations) > 0 else 0,
            total_iterations=self.iterations,
        )

    def summary(self) -> str:
        lines = ["=" * 50, "  BENCHMARK RESULTS", "=" * 50]
        for r in self._results:
            lines.append(f"  {r.name}: {r.duration_ms:.1f}ms | {r.tiles_per_second:.0f} tps | {r.memory_kb:.0f}KB")
        lines.append("=" * 50)
        return "\n".join(lines)