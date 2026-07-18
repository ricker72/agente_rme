"""
Autonomous Visualizer — produces matplotlib visualisations of the
autonomous design loop.

The visualizer is intentionally lightweight: it uses only the standard
library plus matplotlib (which is already a hard dependency of the
project via the preview pipeline).  The plots are:

* ``iteration_scores.png`` — bar chart of every per-iteration score
* ``critic_progress.png``  — line chart of the critic score across
  iterations
* ``optimization_curve.png`` — combined plot of all five scores
"""

from __future__ import annotations

import os
from typing import List

from .models.design_result import DesignResult


def _try_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except Exception:  # pragma: no cover
        return None


class AutonomousVisualizer:
    """Generate PNG visualisations of the autonomous loop."""

    def __init__(self, output_dir: str) -> None:
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plot_iteration_scores(self, result: DesignResult) -> str:
        """Bar chart of per-iteration scores."""
        plt = _try_matplotlib()
        if plt is None or not result.iterations:
            return ""
        iterations = [f"#{i.iteration_id}" for i in result.iterations]
        critic = [i.critic_score for i in result.iterations]
        playtest = [i.playtest_score for i in result.iterations]
        navigation = [i.navigation_score for i in result.iterations]
        density = [i.density_score for i in result.iterations]
        reuse = [i.reuse_score for i in result.iterations]

        fig, ax = plt.subplots(figsize=(8, 4))
        x = list(range(len(iterations)))
        width = 0.18
        ax.bar([xi - 2 * width for xi in x], critic, width, label="critic")
        ax.bar([xi - width for xi in x], playtest, width, label="playtest")
        ax.bar(x, navigation, width, label="navigation")
        ax.bar([xi + width for xi in x], density, width, label="density")
        ax.bar([xi + 2 * width for xi in x], reuse, width, label="reuse")
        ax.set_xticks(x)
        ax.set_xticklabels(iterations, rotation=45)
        ax.set_ylim(0, 1)
        ax.set_ylabel("Score (0-1)")
        ax.set_title(f"Per-iteration scores — result {result.result_id[:8]}")
        ax.legend(loc="lower right", fontsize=8)
        ax.grid(True, axis="y", linestyle="--", alpha=0.3)
        fig.tight_layout()

        path = os.path.join(self.output_dir, "iteration_scores.png")
        fig.savefig(path, dpi=80)
        plt.close(fig)
        return path

    def plot_critic_progress(self, result: DesignResult) -> str:
        """Line chart of the critic score across iterations."""
        plt = _try_matplotlib()
        if plt is None or not result.iterations:
            return ""
        scores: List[float] = [i.critic_score for i in result.iterations]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(range(len(scores)), scores, marker="o", color="tab:blue", linewidth=2)
        if result.iterations:
            target = result.iterations[0].scores.get("critic_target", 0.9)
        else:
            target = 0.9
        ax.axhline(target, color="red", linestyle="--", label=f"target={target:.2f}")
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Critic score (0-1)")
        ax.set_title("Critic progress")
        ax.set_ylim(0, 1)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend()
        fig.tight_layout()

        path = os.path.join(self.output_dir, "critic_progress.png")
        fig.savefig(path, dpi=80)
        plt.close(fig)
        return path

    def plot_optimization_curve(self, result: DesignResult) -> str:
        """Combined plot of all five optimisation scores."""
        plt = _try_matplotlib()
        if plt is None or not result.iterations:
            return ""
        scores = {
            "critic": [i.critic_score for i in result.iterations],
            "playtest": [i.playtest_score for i in result.iterations],
            "navigation": [i.navigation_score for i in result.iterations],
            "density": [i.density_score for i in result.iterations],
            "reuse": [i.reuse_score for i in result.iterations],
        }
        fig, ax = plt.subplots(figsize=(8, 4))
        for name, vals in scores.items():
            ax.plot(range(len(vals)), vals, marker="o", label=name, linewidth=1.5)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Score (0-1)")
        ax.set_title("Optimization curve")
        ax.set_ylim(0, 1)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(loc="lower right", fontsize=8)
        fig.tight_layout()

        path = os.path.join(self.output_dir, "optimization_curve.png")
        fig.savefig(path, dpi=80)
        plt.close(fig)
        return path
