from dataclasses import dataclass
from typing import List, Tuple

DISTRICT_TYPES = [
    "Temple",
    "Depot",
    "Market",
    "Residential",
    "Training",
    "Harbor",
    "Castle",
    "Industrial",
    "HuntingGate",
]


@dataclass
class District:
    name: str
    type: str
    x: int
    y: int
    width: int
    height: int
    description: str = ""

    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


def generate_city_districts(
    city_style: str, origin_x: int, origin_y: int
) -> List[District]:
    base_size = 12
    spread = 18
    return [
        District(
            name="Central Plaza",
            type="Market",
            x=origin_x - base_size // 2,
            y=origin_y - 2,
            width=base_size,
            height=base_size,
            description="Centro comercial con fuente y puestos.",
        ),
        District(
            name="Temple District",
            type="Temple",
            x=origin_x - spread - 6,
            y=origin_y - spread - 3,
            width=10,
            height=10,
            description="Templo sagrado con altar y respawn seguro.",
        ),
        District(
            name="Depot Quarter",
            type="Depot",
            x=origin_x + spread - 4,
            y=origin_y - spread + 1,
            width=10,
            height=8,
            description="Depósito con lockers, inbox y acceso rápido.",
        ),
        District(
            name="Residential Block",
            type="Residential",
            x=origin_x - spread - 2,
            y=origin_y + spread - 2,
            width=14,
            height=10,
            description="Viviendas pequeñas y medianas para habitantes.",
        ),
        District(
            name="Harbor Front",
            type="Harbor",
            x=origin_x + spread - 2,
            y=origin_y + spread - 2,
            width=18,
            height=12,
            description="Puerto con muelles, barcas y accesos a la ciudad.",
        ),
        District(
            name="Training Grounds",
            type="Training",
            x=origin_x - 4,
            y=origin_y + spread + 10,
            width=12,
            height=8,
            description="Zona de entrenamiento y hunting gate de apoyo.",
        ),
    ]
