from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Dict

from .district_generator import District, generate_city_districts
from .road_generator import Road, RoadGenerator
from .building_generator import Building, generate_buildings
from .temple_generator import generate_temple_layout
from .depot_generator import generate_depot_layout
from .market_generator import generate_market_layout
from .harbor_generator import generate_harbor_layout


@dataclass
class Waypoint:
    name: str
    x: int
    y: int
    z: int
    type: str


@dataclass
class City:
    name: str
    theme: str
    size: Tuple[int, int]
    districts: List[District] = field(default_factory=list)
    roads: List[Road] = field(default_factory=list)
    buildings: List[Building] = field(default_factory=list)
    waypoints: List[Waypoint] = field(default_factory=list)
    spawns: List[Dict[str, object]] = field(default_factory=list)


class CityGenerator:
    DEFAULT_TEMPLATE = {
        "roads": [415, 416],
        "floors": [393, 415, 416],
        "walls": [1495, 1496, 1497],
        "decorations": [2153, 2150, 2149],
    }

    CITY_STYLES = ["issavi", "thais", "venore", "yalahar", "carlin", "ankrahmun", "darashia", "edron"]

    def __init__(self, style: str = "issavi", min_level: int = 50, max_level: int = 300):
        self.style = style.lower()
        self.min_level = min_level
        self.max_level = max_level
        self.template = self._load_theme_template(self.style)
        self.city = self._build_city()

    @classmethod
    def from_prompt(cls, prompt: str) -> "CityGenerator":
        style = cls._parse_style(prompt)
        min_level, max_level = cls._parse_level_range(prompt)
        return cls(style=style, min_level=min_level, max_level=max_level)

    @staticmethod
    def _parse_style(prompt: str) -> str:
        lower = prompt.lower()
        for style in CityGenerator.CITY_STYLES:
            if style in lower:
                return style
        if "issavi" in lower:
            return "issavi"
        return "issavi"

    @staticmethod
    def _parse_level_range(prompt: str) -> Tuple[int, int]:
        numbers = re.findall(r"\d+", prompt)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        if len(numbers) == 1:
            return int(numbers[0]), int(numbers[0])
        return 50, 300

    def _load_theme_template(self, style: str) -> Dict[str, List[int]]:
        template_path = Path(__file__).resolve().parents[4] / "templates" / "cities" / f"{style}.json"
        if template_path.exists():
            try:
                return json.loads(template_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return self.DEFAULT_TEMPLATE

    def _build_city(self) -> City:
        base_width = 42
        base_height = 42
        center_x = 100
        center_y = 100
        city = City(
            name=self.style.capitalize(),
            theme=self.style,
            size=(base_width, base_height),
        )

        city.districts = generate_city_districts(self.style, center_x, center_y)
        city.roads = RoadGenerator.connect_districts(city.districts, (center_x, center_y))
        city.buildings = generate_buildings(city.districts, self.template)
        city.spawns = self._generate_spawn_zones(city.districts, center_x, center_y)
        city.waypoints = self._generate_waypoints(city.districts, center_x, center_y)
        return city

    def _generate_spawn_zones(self, districts: List[District], center_x: int, center_y: int) -> List[Dict[str, object]]:
        zones = [
            {"name": "Temple Respawn", "x": center_x - 8, "y": center_y - 10, "z": 7, "radius": 3},
            {"name": "Market Square", "x": center_x, "y": center_y, "z": 7, "radius": 4},
        ]
        return zones

    def _generate_waypoints(self, districts: List[District], center_x: int, center_y: int) -> List[Waypoint]:
        waypoints: List[Waypoint] = []
        waypoints.append(Waypoint(name="Central Plaza", x=center_x, y=center_y, z=7, type="Gate"))
        for district in districts:
            waypoints.append(Waypoint(
                name=district.name,
                x=district.center()[0],
                y=district.center()[1],
                z=7,
                type=district.type,
            ))
        return waypoints

    def generate_lua(self, description: str) -> str:
        z = 7
        lines = [
            "if not app.hasMap() then",
            "  return",
            "end",
            "\napp.transaction(function(map)",
        ]

        lines.append("  local z = 7")
        lines.append("  local function tileAt(x, y)")
        lines.append("    return map:getOrCreateTile(x, y, z)")
        lines.append("  end\n")

        # Roads
        road_ground = self.template.get("roads", [415])[0]
        for road in self.city.roads:
            for x, y in road.path:
                lines.append(f"  tileAt({x}, {y}).ground = {road_ground}")

        # District layouts
        for district in self.city.districts:
            floor = self.template.get("floors", [393])[0]
            for dx in range(district.width):
                for dy in range(district.height):
                    x = district.x + dx
                    y = district.y + dy
                    lines.append(f"  tileAt({x}, {y}).ground = {floor}")

        # Special district content
        for district in self.city.districts:
            if district.type == "Temple":
                for shape in generate_temple_layout(district, self.template):
                    if "ground" in shape:
                        lines.append(f"  tileAt({shape['x']}, {shape['y']}).ground = {shape['ground']}")
                    if "item" in shape:
                        lines.append(f"  tileAt({shape['x']}, {shape['y']}):addItem({shape['item']})")
            elif district.type == "Depot":
                for shape in generate_depot_layout(district, self.template):
                    if "ground" in shape:
                        lines.append(f"  tileAt({shape['x']}, {shape['y']}).ground = {shape['ground']}")
                    if "item" in shape:
                        lines.append(f"  tileAt({shape['x']}, {shape['y']}):addItem({shape['item']})")
            elif district.type == "Market":
                for shape in generate_market_layout(district, self.template):
                    if "ground" in shape:
                        lines.append(f"  tileAt({shape['x']}, {shape['y']}).ground = {shape['ground']}")
                    if "item" in shape:
                        lines.append(f"  tileAt({shape['x']}, {shape['y']}):addItem({shape['item']})")
            elif district.type == "Harbor":
                for shape in generate_harbor_layout(district, self.template):
                    if "ground" in shape:
                        lines.append(f"  tileAt({shape['x']}, {shape['y']}).ground = {shape['ground']}")
                    if "item" in shape:
                        lines.append(f"  tileAt({shape['x']}, {shape['y']}):addItem({shape['item']})")

        # Building outlines and decorations
        for building in self.city.buildings:
            wall = self.template.get("walls", [1495])[0]
            for dx in range(building.width):
                for dy in range(building.height):
                    x = building.x + dx
                    y = building.y + dy
                    lines.append(f"  tileAt({x}, {y}).ground = {self.template.get('floors', [393])[0]}")
            # borderize each building
            for dx in range(building.width):
                lines.append(f"  tileAt({building.x + dx}, {building.y}).borderize()")
                lines.append(f"  tileAt({building.x + dx}, {building.y + building.height - 1}).borderize()")
            for dy in range(building.height):
                lines.append(f"  tileAt({building.x}, {building.y + dy}).borderize()")
                lines.append(f"  tileAt({building.x + building.width - 1}, {building.y + dy}).borderize()")

        # Waypoints and spawn markers
        waypoint_ground = self.template.get("decorations", [2153])[0]
        for waypoint in self.city.waypoints:
            lines.append(f"  tileAt({waypoint.x}, {waypoint.y}).ground = {waypoint_ground}")
        for spawn in self.city.spawns:
            lines.append(f"  tileAt({spawn['x']}, {spawn['y']}).ground = {self.template.get('decorations', [2150])[0]}")

        lines.append("end")
        return "\n".join(lines)

    def supports_prompt(self, prompt: str) -> bool:
        lower = prompt.lower()
        return "ciudad" in lower or any(name in lower for name in self.CITY_STYLES)
