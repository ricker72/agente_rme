class CityGenerator:
    def __init__(self, width: int = 20, height: int = 20, depth: int = 1):
        self.width = width
        self.height = height
        self.depth = depth

    def generate_lua(self, description: str) -> str:
        return (
            "-- City generator script for RME\n"
            "if not app.hasMap() then\n"
            '  error("No hay mapa cargado en RME.")\n'
            "end\n\n"
            "app.transaction(function(map)\n"
            "  -- Crear plazas, calles y edificios principales\n"
            "  local center = { x = 100, y = 100, z = 7 }\n"
            "  local tile = map:getOrCreateTile(center.x, center.y, center.z)\n"
            "  tile:setGround(455) -- piedra pulida\n"
            "end)\n"
        )
