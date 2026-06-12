"""
Reusable custom widgets for Agente RME Studio.
Exports the widgets used on the Dashboard page.
"""

from __future__ import annotations

from .metric_card import MetricCard
from .health_widget import HealthWidget
from .recent_artifacts_widget import RecentArtifactsWidget
from .recent_activity_widget import RecentActivityWidget
from .system_status_widget import SystemStatusWidget
from .release_info_widget import ReleaseInfoWidget

__all__: list[str] = [
    "MetricCard",
    "HealthWidget",
    "RecentArtifactsWidget",
    "RecentActivityWidget",
    "SystemStatusWidget",
    "ReleaseInfoWidget",
]
