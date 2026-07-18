from __future__ import annotations

from typing import Any, Mapping


def lua_quote(value: object) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def generate_world_metadata_lua(integration: Mapping[str, Any]) -> str:
    lines = ["-- WGL-11 deterministic metadata, not gameplay script", "return {", "  constants = {"]
    lines.append(f"    otbm_fingerprint = {lua_quote(integration['otbm_fingerprint'])},")
    lines.append(f"    deployment_ready = {str(bool(integration['deployment_ready'])).lower()},")
    lines.append("  },")
    lines.append("  counts = {")
    for key, value in sorted(integration["counts"].items()):
        lines.append(f"    {key} = {int(value)},")
    lines.append("  },")
    lines.append("}")
    return "\n".join(lines) + "\n"


def generate_navigation_metadata_lua(gameplay: Mapping[str, Any]) -> str:
    nav = gameplay.get("models", {}).get("navigation", {})
    lines = ["-- WGL-11 navigation lookup metadata, not gameplay script", "return {", "  nodes = {"]
    for node in sorted(nav.get("nodes", []), key=lambda item: item["id"]):
        lines.append(f"    [{lua_quote(node['id'])}] = {lua_quote(node.get('accessibility_class', 'public'))},")
    lines.append("  },")
    lines.append("  edges = {")
    for edge in sorted(nav.get("edges", []), key=lambda item: item["id"]):
        lines.append(
            "    { id = "
            + lua_quote(edge["id"])
            + ", from = "
            + lua_quote(edge["from"])
            + ", to = "
            + lua_quote(edge["to"])
            + ", cost = "
            + str(int(edge.get("travel_cost", 0)))
            + " },"
        )
    lines.append("  },")
    lines.append("}")
    return "\n".join(lines) + "\n"
