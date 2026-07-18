"""AI Engineering dock content for proposal-only map workflows."""

from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QPlainTextEdit, QTabWidget


AI_DOCK_TABS = (
    "Prompt Builder",
    "Prompt Library",
    "AI Context",
    "Reference World Knowledge",
    "Proposal Preview",
    "Human Approval",
)


def build_ai_engineering_tabs(reference_profile: dict, asset_health: dict, error: str = "") -> QTabWidget:
    tabs = QTabWidget()
    tabs.setObjectName("UX03AIEngineeringPanel")
    for title in AI_DOCK_TABS:
        if title == "Proposal Preview":
            preview = QPlainTextEdit()
            preview.setObjectName("MEP01ProposalPreview")
            preview.setReadOnly(True)
            preview.setPlainText("AI proposals are preview-only until human approval.")
            tabs.addTab(preview, title)
            continue
        items = QListWidget()
        items.setObjectName(f"PMX01A{title.replace(' ', '')}")
        if title == "AI Context":
            items.addItems(["Current project", "Current coordinates", "Asset Registry", "Reference World Knowledge"])
        elif title == "Reference World Knowledge":
            if reference_profile:
                items.addItem(f"Source: {reference_profile.get('source_path')}")
                items.addItem(f"Sampled tiles: {reference_profile.get('sampled_tile_count')}")
                items.addItem(str(reference_profile.get("copy_policy")))
            else:
                items.addItem(f"Reference world unavailable: {error}")
        elif title == "Human Approval":
            items.addItems(["No direct AI map mutation", "Review proposal", "Approve before apply"])
        elif title == "Prompt Library":
            items.addItems(["Town expansion", "Hunt proposal", "Road connection", "Decoration pass"])
        elif title == "Prompt Builder":
            items.addItems(["User Prompt", "Context Builder", "Asset Registry", "AI Proposal", "Critic Review"])
        else:
            items.addItem(str(asset_health or "Asset health unavailable"))
        tabs.addTab(items, title)
    return tabs
