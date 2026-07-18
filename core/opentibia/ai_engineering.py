"""Prompt enrichment for OpenTibia AI engineering workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PROMPT_LIBRARY = {
    "Cities": "Design an original OpenTibia city district using official assets and validated road connectivity.",
    "Temples": "Create a temple area with safe spawn, town services, and OpenTibia-compatible navigation.",
    "Depots": "Design a depot connected to main roads, shops, and town routes.",
    "NPCs": "Plan NPC placement with service roles and non-blocking pedestrian flow.",
    "Quests": "Draft original quest structure without copying reference-world quests.",
    "Roads": "Create roads with readable tile transitions and route hierarchy.",
    "Bridges": "Design bridge crossings with valid water and road transitions.",
    "Mountains": "Create mountain terrain with ramps, borders, and navigable constraints.",
    "Hunts": "Design original hunt loops inspired by gameplay complexity, not copied layout.",
    "Boss Arenas": "Create boss arena topology with entry, exit, safety, and encounter zones.",
    "Decoration": "Decorate using official assets with density and readability constraints.",
    "Optimization": "Optimize map density, pathing, and editor performance.",
    "Validation": "Validate OpenTibia/RME/Canary/TFS/OTClient compatibility before applying.",
}


@dataclass(frozen=True)
class PromptContext:
    project: str
    town: str
    coordinates: str
    selected_asset: str
    selection: str
    asset_summary: str
    reference_summary: str
    constraints: tuple[str, ...]
    planner_summary: str = "Planner unavailable"


class PromptBuilder:
    """Builds enriched prompts; the raw user prompt is never sent alone."""

    def build(self, raw_prompt: str, context: PromptContext, template: str = "Hunts") -> str:
        template_text = PROMPT_LIBRARY.get(template, PROMPT_LIBRARY["Validation"])
        lines = [
            "RME AI Studio OpenTibia Engineering Prompt",
            "",
            f"Template: {template}",
            f"Template intent: {template_text}",
            "",
            "Current context:",
            f"- Project: {context.project}",
            f"- Town: {context.town}",
            f"- Coordinates: {context.coordinates}",
            f"- Selection: {context.selection}",
            f"- Selected asset: {context.selected_asset}",
            f"- Asset Registry: {context.asset_summary}",
            f"- Reference World: {context.reference_summary}",
            f"- Mapper Planner: {context.planner_summary}",
            "",
            "Engineering constraints:",
        ]
        lines.extend(f"- {constraint}" for constraint in context.constraints)
        lines.extend(
            [
                "",
                "User request:",
                raw_prompt.strip(),
                "",
                "Output required:",
                "- Return an original OpenTibia-compatible proposal.",
                "- Do not copy or reproduce reference-world layouts.",
                "- Use only official Asset Registry assets.",
                "- Wait for human approval before applying changes.",
            ]
        )
        return "\n".join(lines)


def context_from_workspace(
    *,
    project: str,
    town: str,
    coordinates: str,
    selected_asset: str,
    selection: str,
    asset_health: dict[str, Any],
    reference_profile: dict[str, Any],
    planner_summary: str = "Planner unavailable",
) -> PromptContext:
    return PromptContext(
        project=project,
        town=town,
        coordinates=coordinates,
        selected_asset=selected_asset,
        selection=selection,
        asset_summary=(
            f"{asset_health.get('asset_count', 0)} assets, "
            f"{asset_health.get('category_count', 0)} categories, "
            f"{asset_health.get('brush_count', 0)} brushes"
        ),
        reference_summary=(
            f"{reference_profile.get('file_size', 0)} bytes, "
            f"{reference_profile.get('sampled_tile_count', 0)} sampled tiles, "
            f"copy policy: {reference_profile.get('copy_policy', 'patterns only')}"
        ),
        planner_summary=planner_summary,
        constraints=(
            "OpenTibia-only.",
            "Preserve OTBM/RME/Canary/TFS/OTServBR/OTClient compatibility.",
            "Use official assets only.",
            "Learn patterns, never copy maps.",
            "Human approval is required before applying.",
        ),
    )
