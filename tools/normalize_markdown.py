"""Normalize project Markdown spacing and unordered list markers."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
LIST_RE = re.compile(r"^(\s*)[-+]\s+(.+)$")
NORMALIZED_LIST_RE = re.compile(r"^\s*\*\s+")


def _newline_for(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _split_preserving_final_newline(text: str) -> tuple[list[str], bool]:
    return text.splitlines(), text.endswith(("\n", "\r"))


def _is_fence(line: str) -> bool:
    return FENCE_RE.match(line) is not None


def _is_heading(line: str) -> bool:
    return HEADING_RE.match(line) is not None


def _is_list_item(line: str) -> bool:
    return NORMALIZED_LIST_RE.match(line) is not None


def _normalize_markers(lines: list[str]) -> list[str]:
    normalized: list[str] = []
    in_fence = False
    in_front_matter = False

    for index, line in enumerate(lines):
        stripped = line.strip()

        if index == 0 and stripped == "---":
            in_front_matter = True
            normalized.append(line)
            continue

        if in_front_matter:
            normalized.append(line)
            if index > 0 and stripped == "---":
                in_front_matter = False
            continue

        if _is_fence(line):
            in_fence = not in_fence
            normalized.append(line)
            continue

        if not in_fence:
            match = LIST_RE.match(line)
            if match:
                line = f"{match.group(1)}* {match.group(2)}"

        normalized.append(line)

    return normalized


def _ensure_blank_before(output: list[str]) -> None:
    if output and output[-1].strip():
        output.append("")


def _normalize_spacing(lines: list[str]) -> list[str]:
    output: list[str] = []
    in_fence = False
    in_front_matter = False
    previous_was_list = False

    for index, line in enumerate(lines):
        stripped = line.strip()

        if index == 0 and stripped == "---":
            in_front_matter = True
            output.append(line)
            previous_was_list = False
            continue

        if in_front_matter:
            output.append(line)
            if index > 0 and stripped == "---":
                in_front_matter = False
            previous_was_list = False
            continue

        fence_line = _is_fence(line)
        heading_line = not in_fence and _is_heading(line)
        list_line = not in_fence and _is_list_item(line)

        if not list_line and previous_was_list and stripped:
            output.append("")

        fence_opener = fence_line and not in_fence

        if heading_line or fence_opener or (list_line and not previous_was_list):
            _ensure_blank_before(output)

        output.append(line)

        if fence_line:
            in_fence = not in_fence
            next_line = lines[index + 1] if index + 1 < len(lines) else ""
            if not in_fence and next_line.strip():
                output.append("")

        if heading_line:
            next_line = lines[index + 1] if index + 1 < len(lines) else ""
            if next_line.strip():
                output.append("")

        previous_was_list = list_line

    return output


def normalize_markdown(text: str) -> str:
    newline = _newline_for(text)
    lines, had_final_newline = _split_preserving_final_newline(text)
    lines = _normalize_markers(lines)
    lines = _normalize_spacing(lines)
    result = newline.join(lines)
    if had_final_newline:
        result += newline
    return result


def normalize_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    normalized = normalize_markdown(original)
    if normalized == original:
        return False
    path.write_text(normalized, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    modified = []
    for path in args.paths:
        if path.suffix.lower() != ".md":
            continue
        if normalize_file(path):
            modified.append(str(path))

    for path in modified:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
