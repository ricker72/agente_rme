local RME = {}

function RME.setGround(tile, itemId)
    tile.ground = itemId
end

function RME.addItem(tile, itemId)
    tile:addItem(itemId)
end

function RME.spawnMonster(map, name, x, y, z, respawnTime)
    local tile = map:getOrCreateTile(x, y, z)
    tile:setCreature(name, respawnTime, Direction.SOUTH)
    return tile
end

function RME.createRoom(map, x1, y1, x2, y2, z, floorId, wallId)
    for x = x1, x2 do
        for y = y1, y2 do
            local tile = map:getOrCreateTile(x, y, z)
            if x == x1 or x == x2 or y == y1 or y == y2 then
                tile.ground = wallId
            else
                tile.ground = floorId
            end
        end
    end
end

function RME.createTemple(map, centerX, centerY, z)
    RME.createRoom(map, centerX - 4, centerY - 4, centerX + 4, centerY + 4, z, 415, 1495)
    local altar = map:getOrCreateTile(centerX, centerY, z)
    altar:addItem(1803)
end

function RME.createRoad(map, x1, y1, x2, y2, z, floorId)
    for x = x1, x2 do
        local tile = map:getOrCreateTile(x, y1, z)
        tile.ground = floorId
    end
    for y = y1, y2 do
        local tile = map:getOrCreateTile(x1, y, z)
        tile.ground = floorId
    end
end

function RME.createCircle(map, centerX, centerY, radius, z, floorId)
    for x = centerX - radius, centerX + radius do
        for y = centerY - radius, centerY + radius do
            local dx = x - centerX
            local dy = y - centerY
            if dx * dx + dy * dy <= radius * radius then
                local tile = map:getOrCreateTile(x, y, z)
                tile.ground = floorId
            end
        end
    end
end

function RME.createRectangle(map, x1, y1, x2, y2, z, floorId)
    for x = x1, x2 do
        for y = y1, y2 do
            local tile = map:getOrCreateTile(x, y, z)
            tile.ground = floorId
        end
    end
end

function RME.borderizeArea(map, x1, y1, x2, y2, z)
    for x = x1, x2 do
        for y = y1, y2 do
            if x == x1 or x == x2 or y == y1 or y == y2 then
                local tile = map:getOrCreateTile(x, y, z)
                tile:borderize()
            end
        end
    end
end

return RME
