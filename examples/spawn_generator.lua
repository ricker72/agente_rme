-- Spawn Generator for OpenTibiaBR RME
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local originX, originY, z = 140, 90, 7

    local spawns = {
        {name = "Frazzlemaw", x = originX, y = originY, time = 30000},
        {name = "Cloak Of Terror", x = originX + 4, y = originY, time = 45000},
        {name = "Sphinx", x = originX + 8, y = originY, time = 60000},
    }

    for _, spawn in ipairs(spawns) do
        local tile = map:getOrCreateTile(spawn.x, spawn.y, z)
        tile.ground = 415
        tile:setCreature(spawn.name, spawn.time, Direction.SOUTH)
    end

    local center = map:getOrCreateTile(originX + 4, originY + 4, z)
    center:setSpawn(3)
end)
