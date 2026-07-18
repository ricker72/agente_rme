from __future__ import annotations

from typing import Any, Dict, Mapping


def plan_economy_population(inputs: Mapping[str, Any], services: Mapping[str, Any]) -> Dict[str, Any]:
    infrastructure = inputs["CERTIFIED_INFRASTRUCTURE_GRAPH.json"]
    routes = infrastructure.get("port_transport_model", {}).get("caravan_routes", [])
    trade_routes = []
    for route in sorted(routes, key=lambda item: item["id"]):
        trade_routes.append(
            {
                "id": f"economy_{route['id']}",
                "from": route.get("from"),
                "to": route.get("to"),
                "merchant_influence": "regional",
                "commercial_importance": "high" if "sunport" in route["id"] else "medium",
            }
        )
    service_count = len(services["services"])
    return {
        "artifact": "ECONOMY_POPULATION_MODEL",
        "logical_only": True,
        "trade_routes": trade_routes,
        "service_density": "complete" if service_count else "none",
        "service_count": service_count,
    }
