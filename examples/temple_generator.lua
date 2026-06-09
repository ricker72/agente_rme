-- Temple Generator for OpenTibiaBR RME
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local centerX, centerY, z = 120, 100, 7
    local size = 9

    for dx = -size, size do
        for dy = -size, size do
            local x, y = centerX + dx, centerY + dy
            local tile = map:getOrCreateTile(x, y, z)
            if math.abs(dx) == size or math.abs(dy) == size then
                tile.ground = 1495
            else
                tile.ground = 415
            end
        end
    end

    local altar = map:getOrCreateTile(centerX, centerY, z)
    altar:addItem(1803)
    altar:borderize()
    app.setCameraPosition(centerX, centerY, z)
end)
