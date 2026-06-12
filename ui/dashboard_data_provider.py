"""
Dashboard Data Provider for Agente RME Studio.

Responsible for reading JSON files, validating data, and converting to DTOs.
Never reads files directly from widgets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class MetricCardDTO:
    """Data Transfer Object for a metric card."""

    title: str = "Unknown"
    value: str = "No Data"
    icon: str = ""


@dataclass
class ArtifactDTO:
    """Data Transfer Object for a recent artifact."""

    name: str = ""
    path: str = ""
    modified: str = ""
    size: str = ""


@dataclass
class ActivityDTO:
    """Data Transfer Object for a recent activity item."""

    label: str = ""
    timestamp: str = "No Data"


@dataclass
class HealthDTO:
    """Data Transfer Object for health status."""

    healthy: int = 0
    warning: int = 0
    error: int = 0


@dataclass
class ReleaseInfoDTO:
    """Data Transfer Object for release information."""

    name: str = "RME Agente AI"
    version: str = "v1.0.0 GA"


@dataclass
class SystemStatusDTO:
    """Data Transfer Object for system status."""

    ui_status: str = "ONLINE"
    dashboard_status: str = "ONLINE"
    plugin_status: str = "ONLINE"
    event_bus_status: str = "ONLINE"


@dataclass
class DashboardData:
    """Complete dashboard data container."""

    metrics: List[MetricCardDTO] = field(default_factory=list)
    health: HealthDTO = field(default_factory=HealthDTO)
    artifacts: List[ArtifactDTO] = field(default_factory=list)
    activity: List[ActivityDTO] = field(default_factory=list)
    release_info: ReleaseInfoDTO = field(default_factory=ReleaseInfoDTO)
    system_status: SystemStatusDTO = field(default_factory=SystemStatusDTO)


class DashboardDataProvider:
    """Provides data for the dashboard by reading JSON files from output/."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        self._base_dir = Path(base_dir) if base_dir else Path.cwd()
        self._output_dir = self._base_dir / "output"

    def _read_json(self, filename: str) -> dict:
        """Read a JSON file and return its contents.

        Returns empty dict if file not found or invalid JSON.
        """
        filepath = self._output_dir / filename
        if not filepath.exists():
            filepath = self._base_dir / filename

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                result: dict[str, object] = json.load(f)  # type: ignore[assignment]
                return result
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            return {}

    def _get_file_info(self, filepath: Path) -> Optional[ArtifactDTO]:
        """Get file info for an artifact."""
        if not filepath.exists():
            return None

        stat = filepath.stat()
        from datetime import datetime

        mod_time = datetime.fromtimestamp(stat.st_mtime)

        size_bytes = stat.st_size
        if size_bytes > 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        elif size_bytes > 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes} B"

        return ArtifactDTO(
            name=filepath.name,
            path=str(filepath),
            modified=mod_time.strftime("%Y-%m-%d %H:%M"),
            size=size_str,
        )

    def get_metrics(self) -> List[MetricCardDTO]:
        """Get metric cards data from various JSON sources."""
        metrics = []

        # Worlds Generated - count OTBM files
        otbm_files = list(self._output_dir.glob("*.otbm"))
        metrics.append(
            MetricCardDTO(
                title="Worlds Generated", value=str(len(otbm_files)), icon="world"
            )
        )

        # Knowledge Entries
        knowledge_data = self._read_json("knowledge_metrics.json")
        total_entries = knowledge_data.get("total_entries", 0)
        metrics.append(
            MetricCardDTO(
                title="Knowledge Entries", value=str(total_entries), icon="book"
            )
        )

        # Critic Score
        critic_data = self._read_json("critic.json")
        critic_score = critic_data.get("score", "No Data")
        if isinstance(critic_score, (int, float)):
            critic_score = f"{critic_score:.1f}%"
        metrics.append(
            MetricCardDTO(
                title="Critic Score",
                value=str(critic_score) if critic_score else "No Data",
                icon="star",
            )
        )

        # Success Rate
        agent_data = self._read_json("agent_metrics.json")
        success_rate = agent_data.get("agent_success_rate", "No Data")
        if isinstance(success_rate, (int, float)):
            success_rate = f"{success_rate:.1f}%"
        metrics.append(
            MetricCardDTO(
                title="Success Rate",
                value=str(success_rate) if success_rate else "No Data",
                icon="check",
            )
        )

        # OTBM Exports
        metrics.append(
            MetricCardDTO(
                title="OTBM Exports", value=str(len(otbm_files)), icon="export"
            )
        )

        # Campaigns Generated
        campaign_data = self._read_json("campaign.json")
        campaign_count = 1 if campaign_data else 0
        metrics.append(
            MetricCardDTO(
                title="Campaigns Generated", value=str(campaign_count), icon="campaign"
            )
        )

        return metrics

    def get_health(self) -> HealthDTO:
        """Get health status from health_report.json."""
        health_data = self._read_json("health_report.json")

        if not health_data:
            return HealthDTO(healthy=0, warning=0, error=0)

        status = health_data.get("status", "unknown").lower()

        if status == "healthy":
            return HealthDTO(healthy=1, warning=0, error=0)
        elif status == "warning":
            return HealthDTO(healthy=0, warning=1, error=0)
        elif status == "error":
            return HealthDTO(healthy=0, warning=0, error=1)

        return HealthDTO(healthy=0, warning=0, error=0)

    def get_artifacts(self) -> List[ArtifactDTO]:
        """Get list of recent artifacts from output directory."""
        artifacts = []

        target_files = [
            "generated.otbm",
            "generated.lua",
            "campaign.json",
            "critic_report.json",
            "critic.json",
            "knowledge_dataset.json",
            "preview.png",
            "agent_metrics.json",
            "knowledge_metrics.json",
            "report.json",
        ]

        for filename in target_files:
            filepath = self._output_dir / filename
            artifact = self._get_file_info(filepath)
            if artifact:
                artifacts.append(artifact)

        # Sort by modification time (newest first)
        artifacts.sort(key=lambda a: a.modified, reverse=True)

        return artifacts[:10]

    def get_activity(self) -> List[ActivityDTO]:
        """Get recent activity based on file timestamps."""
        activities = []

        activity_map = {
            "Last Export": ["generated.otbm", "e2e_test.otbm"],
            "Last Critic": ["critic.json", "critic_report.json"],
            "Last Knowledge Build": [
                "knowledge_dataset.json",
                "knowledge_metrics.json",
            ],
            "Last Campaign": ["campaign.json"],
        }

        from datetime import datetime

        for label, filenames in activity_map.items():
            timestamp = "No Data"
            for filename in filenames:
                filepath = self._output_dir / filename
                if filepath.exists():
                    mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                    timestamp = mod_time.strftime("%Y-%m-%d %H:%M")
                    break
            activities.append(ActivityDTO(label=label, timestamp=timestamp))

        return activities

    def get_release_info(self) -> ReleaseInfoDTO:
        """Get release information."""
        name = "RME Agente AI"
        version = "v1.0.0 GA"

        # Try to read version from VERSION file
        version_file = self._base_dir / "VERSION"
        if version_file.exists():
            try:
                version = version_file.read_text(encoding="utf-8").strip()
                if version:
                    return ReleaseInfoDTO(name=name, version=version)
            except (PermissionError, OSError):
                pass

        # Try to read from version.py
        version_py = self._base_dir / "version.py"
        if version_py.exists():
            try:
                content = version_py.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if "version" in line.lower() and "=" in line:
                        version = line.split("=")[1].strip().strip('"').strip("'")
                        if version:
                            return ReleaseInfoDTO(name=name, version=version)
            except (PermissionError, OSError):
                pass

        # Try to read from pyproject.toml
        pyproject = self._base_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                in_project = False
                for line in content.splitlines():
                    if "[project]" in line:
                        in_project = True
                    elif line.startswith("["):
                        in_project = False
                    elif in_project and "version" in line:
                        parts = line.split("=")
                        if len(parts) >= 2:
                            version = parts[1].strip().strip('"').strip("'")
                            if version:
                                return ReleaseInfoDTO(name=name, version=f"v{version}")
            except (PermissionError, OSError):
                pass

        return ReleaseInfoDTO(name=name, version=version)

    def get_system_status(self) -> SystemStatusDTO:
        """Get system status (always ONLINE for dashboard)."""
        return SystemStatusDTO(
            ui_status="ONLINE",
            dashboard_status="ONLINE",
            plugin_status="ONLINE",
            event_bus_status="ONLINE",
        )

    def get_all_data(self) -> DashboardData:
        """Get all dashboard data at once."""
        return DashboardData(
            metrics=self.get_metrics(),
            health=self.get_health(),
            artifacts=self.get_artifacts(),
            activity=self.get_activity(),
            release_info=self.get_release_info(),
            system_status=self.get_system_status(),
        )
