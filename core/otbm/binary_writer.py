"""
OTBM binary writer — safe range-validated struct.pack helpers.

This module centralises ALL struct.pack operations used by the OTBM
encoder, providing:

  * Pre-validation of every value (0 <= uint8 <= 255, 0 <= uint16 <= 65535, …)
  * Automatic clamping of out-of-range values with a descriptive warning
  * Identical API to NodeEncoder._write_uintN (so refactor is drop-in)
  * Centralised error handling so the rest of the pipeline can be confident
    that no `struct.error: 'B' format requires 0 <= number <= 255` is ever
    raised by the OTBM export code.

Usage:
    from core.otbm.binary_writer import BinaryWriter
    bw = BinaryWriter()
    bw.write_u8(buf, 300)         # -> writes 255 + warning
    bw.write_u16(buf, 999999)     # -> writes 65535 + warning
"""

from __future__ import annotations

import io
import struct
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BinaryWriter:
    """Range-validated writer for OTBM binary primitives."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write_u8(self, buf: io.BytesIO, value: int, *, context: str = "u8") -> int:
        """Write a uint8 to ``buf``, clamping to [0, 255] with a warning.

        Args:
            buf: Target buffer.
            value: Integer to write.
            context: Description used in the warning (e.g. "ground_id").

        Returns:
            The value that was actually written (always 0..255).
        """
        coerced = self._coerce(value, 0, 255, context)
        buf.write(struct.pack("<B", coerced))
        return coerced

    def write_u16(self, buf: io.BytesIO, value: int, *, context: str = "u16") -> int:
        """Write a uint16 to ``buf``, clamping to [0, 65535] with a warning."""
        coerced = self._coerce(value, 0, 65535, context)
        buf.write(struct.pack("<H", coerced))
        return coerced

    def write_u32(self, buf: io.BytesIO, value: int, *, context: str = "u32") -> int:
        """Write a uint32 to ``buf``, clamping to [0, 2**32-1] with a warning."""
        coerced = self._coerce(value, 0, 0xFFFFFFFF, context)
        buf.write(struct.pack("<I", coerced))
        return coerced

    def write_string(self, buf: io.BytesIO, text: str, *, max_len: int = 65535) -> int:
        """Write a length-prefixed UTF-8 string.

        Truncates ``text`` to ``max_len`` bytes and emits a warning if
        truncation actually happened.

        Returns:
            The number of bytes written (header + payload).
        """
        try:
            encoded = (text or "").encode("utf-8", errors="ignore")
        except Exception:  # pragma: no cover — defensive
            encoded = b""

        if len(encoded) > max_len:
            logger.warning(
                "BinaryWriter.write_string truncating %d -> %d bytes",
                len(encoded), max_len,
            )
            encoded = encoded[:max_len]

        buf.write(struct.pack("<H", len(encoded)))
        buf.write(encoded)
        return 2 + len(encoded)

    def write_signed_byte(self, buf: io.BytesIO, value: int, *, context: str = "i8") -> int:
        """Write a signed int8 to ``buf``, clamping to [-128, 127]."""
        coerced = self._coerce(value, -128, 127, context)
        buf.write(struct.pack("<b", coerced))
        return coerced

    def write_i32(self, buf: io.BytesIO, value: int, *, context: str = "i32") -> int:
        """Write a signed int32 to ``buf`` with validation."""
        coerced = self._coerce(value, -0x80000000, 0x7FFFFFFF, context)
        buf.write(struct.pack("<i", coerced))
        return coerced

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def validate_u8(value: int, context: str = "u8") -> int:
        """Validate a value is a valid uint8, raising ValueError otherwise."""
        if value is None:
            raise ValueError(f"{context}: value is None")
        if not isinstance(value, (int,)):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ValueError(f"{context}: cannot convert {value!r} to int")
        if value < 0 or value > 255:
            raise ValueError(
                f"{context}: value {value} out of uint8 range [0, 255]"
            )
        return int(value)

    @staticmethod
    def validate_u16(value: int, context: str = "u16") -> int:
        """Validate a value is a valid uint16, raising ValueError otherwise."""
        if value is None:
            raise ValueError(f"{context}: value is None")
        if not isinstance(value, (int,)):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ValueError(f"{context}: cannot convert {value!r} to int")
        if value < 0 or value > 65535:
            raise ValueError(
                f"{context}: value {value} out of uint16 range [0, 65535]"
            )
        return int(value)

    @staticmethod
    def validate_u32(value: int, context: str = "u32") -> int:
        """Validate a value is a valid uint32, raising ValueError otherwise."""
        if value is None:
            raise ValueError(f"{context}: value is None")
        if not isinstance(value, (int,)):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ValueError(f"{context}: cannot convert {value!r} to int")
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError(
                f"{context}: value {value} out of uint32 range [0, 4294967295]"
            )
        return int(value)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce(value: Any, lo: int, hi: int, context: str) -> int:
        """Clamp ``value`` to [lo, hi] and log a warning if changed.

        Returns the original value (as int) when in range, otherwise the
        clamped value. ``None`` is treated as 0.
        """
        if value is None:
            logger.warning("BinaryWriter: %s was None, using 0", context)
            return 0
        try:
            iv = int(value)
        except (TypeError, ValueError):
            logger.warning(
                "BinaryWriter: %s value %r is not numeric, using 0", context, value
            )
            return 0
        if iv < lo or iv > hi:
            clamped = max(lo, min(hi, iv))
            logger.warning(
                "BinaryWriter: %s value %d out of [%d,%d], clamped to %d",
                context, iv, lo, hi, clamped,
            )
            return clamped
        return iv


# ----------------------------------------------------------------------
# Module-level convenience functions (compatible with struct.pack).
# These are the recommended public surface for new code.
# ----------------------------------------------------------------------

_DEFAULT_WRITER = BinaryWriter()


def write_uint8(buf: io.BytesIO, value: int, context: str = "u8") -> int:
    return _DEFAULT_WRITER.write_u8(buf, value, context=context)


def write_uint16(buf: io.BytesIO, value: int, context: str = "u16") -> int:
    return _DEFAULT_WRITER.write_u16(buf, value, context=context)


def write_uint32(buf: io.BytesIO, value: int, context: str = "u32") -> int:
    return _DEFAULT_WRITER.write_u32(buf, value, context=context)


def write_string(buf: io.BytesIO, text: str, max_len: int = 65535) -> int:
    return _DEFAULT_WRITER.write_string(buf, text, max_len=max_len)
