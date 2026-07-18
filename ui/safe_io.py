"""UI-facing persistence boundary."""

from core.safe_io import SafeIOError, atomic_write_text

__all__ = ["SafeIOError", "atomic_write_text"]
