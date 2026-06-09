from __future__ import annotations

from typing import Dict, List, Tuple


class WorldValidator:
    def validate(self, world_plan: Dict[str, object]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        cities = world_plan.get("cities", [])
        dungeons = world_plan.get("dungeons", [])
        roads = world_plan.get("roads", [])

        if not cities:
            errors.append("El plan debe incluir al menos una ciudad.")
        if not dungeons:
            errors.append("El plan debe incluir al menos una dungeons.")
        if cities and dungeons and not roads:
            errors.append("Necesita rutas que conecten ciudades y dungeons.")

        if len(cities) > 1 and len(roads) < len(cities) - 1:
            errors.append("Debe haber rutas suficientes para conectar todas las ciudades.")

        for city in cities:
            if city.get("population", 0) < 100:
                errors.append(f"La ciudad {city.get('name')} tiene población demasiado baja.")

        for dungeon in dungeons:
            if dungeon.get("difficulty") not in ["easy", "medium", "hard", "extreme"]:
                errors.append(f"La dificultad de {dungeon.get('name')} no es válida.")

        return (len(errors) == 0, errors)
