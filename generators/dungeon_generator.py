class DungeonGenerator:
    def __init__(self, width: int = 16, height: int = 16, depth: int = 1):
        self.width = width
        self.height = height
        self.depth = depth

    def generate_lua(self, description: str) -> str:
        return (
            "-- Dungeon generator script for RME\n"
            "if not app.hasMap() then\n"
            '  error("No hay mapa cargado en RME.")\n'
            "end\n\n"
            "app.transaction(function(map)\n"
            "  -- Crear habitaciones subterráneas y corredores\n"
            "  local z = 7\n"
            "  for x = 100, 105 do\n"
            "    for y = 100, 105 do\n"
            "      local tile = map:getOrCreateTile(x, y, z)\n"
            "      tile:setGround(1292) -- piedra de mazmorra\n"
            "    end\n"
            "  end\n"
            "end)\n"
        )
