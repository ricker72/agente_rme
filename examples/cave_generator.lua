-- Cave Generator for OpenTibiaBR RME
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local originX, originY, z = 90, 90, 7
    local width, height = 24, 18

    for dx = 0, width - 1 do
        for dy = 0, height - 1 do
            local x, y = originX + dx, originY + dy
            local noiseValue = noise.simplex(x * 0.18, y * 0.18, 0)
            local tile = map:getOrCreateTile(x, y, z)
            if noiseValue > 0.05 then
                tile.ground = 393
            else
                tile.ground = 415
            end
            if noiseValue > 0.3 then
                tile:addItem(2148)
            end
        end
    end
end)
