-- Issavi / Roshamuul Hybrid Generator for OpenTibiaBR RME
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local z = 7
    local baseX, baseY = 100, 100

    -- Zona de ruinas Issavi
    for dx = -8, 8 do
        for dy = -6, 6 do
            local x, y = baseX + dx, baseY + dy
            local tile = map:getOrCreateTile(x, y, z)
            if math.abs(dx) == 8 or math.abs(dy) == 6 then
                tile.ground = 1495
            else
                tile.ground = 415
            end
        end
    end

    -- Zona de corrupción Roshamuul
    for dx = -5, 5 do
        for dy = 8, 14 do
            local x, y = baseX + dx, baseY + dy
            local tile = map:getOrCreateTile(x, y, z)
            local noiseValue = noise.simplex(x * 0.2, y * 0.2, 0)
            if noiseValue > 0.1 then
                tile.ground = 1053
            else
                tile.ground = 1056
            end
        end
    end

    -- Arena del jefe
    for dx = -4, 4 do
        for dy = 18, 24 do
            local x, y = baseX + dx, baseY + dy
            local tile = map:getOrCreateTile(x, y, z)
            tile.ground = 393
        end
    end

    local bossTile = map:getOrCreateTile(baseX, baseY + 21, z)
    bossTile:setCreature("Sphinx", 120000, Direction.SOUTH)
    bossTile:borderize()

    -- Spawns clave
    local frazz = map:getOrCreateTile(baseX - 6, baseY + 10, z)
    frazz:setCreature("Frazzlemaw", 60000, Direction.SOUTH)

    local cloak = map:getOrCreateTile(baseX + 6, baseY + 10, z)
    cloak:setCreature("Cloak Of Terror", 75000, Direction.SOUTH)

    local spawnCenter = map:getOrCreateTile(baseX, baseY + 12, z)
    spawnCenter:setSpawn(4)
end)

if app.hasMap() then
    app.setCameraPosition(baseX, baseY + 12, z)
end
