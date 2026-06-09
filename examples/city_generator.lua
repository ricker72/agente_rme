-- City Generator for OpenTibiaBR RME
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local originX, originY, z = 80, 120, 7
    local width, height = 20, 14

    for dx = 0, width - 1 do
        for dy = 0, height - 1 do
            local x, y = originX + dx, originY + dy
            local tile = map:getOrCreateTile(x, y, z)
            if dx == 0 or dy == 0 or dx == width - 1 or dy == height - 1 then
                tile.ground = 1495
            else
                tile.ground = 415
            end
        end
    end

    for roadX = originX + 2, originX + width - 3 do
        local roadTile = map:getOrCreateTile(roadX, originY + 7, z)
        roadTile.ground = 393
    end

    for roofY = originY + 2, originY + height - 3, 4 do
        local wallTile = map:getOrCreateTile(originX + 4, roofY, z)
        wallTile:addItem(1497)
    end
end)
