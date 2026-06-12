from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectVersion:
    """Semantic versioning for Agente RME."""

    major: int
    minor: int
    patch: int = 0
    label: str = ""

    def __str__(self) -> str:
        base = f"v{self.major}.{self.minor}"
        if self.patch:
            base += f".{self.patch}"
        if self.label:
            base += f"-{self.label}"
        return base

    @classmethod
    def current(cls) -> "ProjectVersion":
        return cls(major=1, minor=0, patch=0)

    @classmethod
    def parse(cls, version_str: str) -> "ProjectVersion":
        v = version_str.lstrip("vV")
        parts = v.split("-")
        nums = parts[0].split(".")
        label = parts[1] if len(parts) > 1 else ""
        major = int(nums[0]) if len(nums) > 0 else 0
        minor = int(nums[1]) if len(nums) > 1 else 0
        patch = int(nums[2]) if len(nums) > 2 else 0
        return cls(major=major, minor=minor, patch=patch, label=label)

    @property
    def is_stable(self) -> bool:
        return self.major >= 1 and not self.label

    @property
    def is_prerelease(self) -> bool:
        return bool(self.label)

    def next_minor(self) -> "ProjectVersion":
        return ProjectVersion(major=self.major, minor=self.minor + 1)

    def next_patch(self) -> "ProjectVersion":
        return ProjectVersion(major=self.major, minor=self.minor, patch=self.patch + 1)

    def to_dict(self) -> dict:
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "label": self.label,
            "string": str(self),
        }


__version__ = str(ProjectVersion.current())
VERSION = ProjectVersion.current()
