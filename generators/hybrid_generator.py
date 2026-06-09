class HybridGenerator:
    def generate_lua(self, description: str) -> str:
        return (
            "-- Hybrid map generator script for RME\n"
            "if not app.hasMap() then\n"
            "  error(\"No hay mapa cargado en RME.\")\n"
            "end\n\n"
            "app.transaction(function(map)\n"
            "  -- Genera un entorno mixto con ciudad y mazmorra\n"
            "  local z = 7\n"
            "  local tile = map:getOrCreateTile(100, 100, z)\n"
            "  tile:setGround(455)\n"
            "  local dungeon = map:getOrCreateTile(110, 110, z)\n"
            "  dungeon:setGround(1292)\n"
            "end)\n"
        )
