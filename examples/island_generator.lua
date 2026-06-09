-- Island Generator for OpenTibiaBR RME
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local centerX, centerY, z = 100, 100, 7
    local radius = 8

    for dx = -radius, radius do
        for dy = -radius, radius do
            local x, y = centerX + dx, centerY + dy
            local tile = map:getOrCreateTile(x, y, z)
            if math.abs(dx) == radius or math.abs(dy) == radius then
                tile.ground = 415
            else
                tile.ground = 393
            end
            if dx % 3 == 0 and dy % 3 == 0 and geo.randomScatter(x, y, 0.18) then
                tile:addItem(2148)
            end
        end
    end

    local borderTile = map:getOrCreateTile(centerX - radius, centerY, z)
    borderTile:borderize()
end)
