if not app.hasMap() then
    return
end

local map = app.map

app.transaction()

local tile = map:getOrCreateTile(1000,1000,7)

tile:addItem(2160)