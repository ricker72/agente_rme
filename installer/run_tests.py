"""
RME Map AI Agent v2.0 — Test Runner

Runs all tests with coverage reporting.

Usage:
    python installer/run_tests.py
    python installer/run_tests.py --coverage
    python installer/run_tests.py --verbose
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_tests(coverage=False, verbose=False, min_coverage=80):
    cmd = [sys.executable, "-m", "pytest"]

    if coverage:
        cmd.extend([
            "--cov=core",
            "--cov=cli",
            f"--cov-fail-under={min_coverage}",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
        ])

    if verbose:
        cmd.append("-v")

    cmd.append("tests/")

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RME Agent Test Runner")
    parser.add_argument("--coverage", action="store_true", help="Enable coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--min-coverage", type=int, default=80, help="Minimum coverage threshold")
    args = parser.parse_args()

    code = run_tests(
        coverage=args.coverage,
        verbose=args.verbose,
        min_coverage=args.min_coverage,
    )
    sys.exit(code)