if not app.hasMap() then
    return
end

local map = app.map

app.transaction()

local centerX = 1000
local centerY = 1000
local z = 7

-- Suelo del campamento 5x5
for x = centerX - 2, centerX + 2 do
    for y = centerY - 2, centerY + 2 do
        local tile = map:getOrCreateTile(x, y, z)
        tile.ground = 415
    end
end

-- Paredes en las esquinas
for x = centerX - 2, centerX + 2, 4 do
    for y = centerY - 2, centerY + 2, 4 do
        local wall = map:getOrCreateTile(x, y, z)
        wall:addItem(1495)
    end
end

-- Fogata central
local fire = map:getOrCreateTile(centerX, centerY, z)
fire:addItem(1765)

-- Spawn de rata cerca
local rat = map:getOrCreateTile(centerX - 1, centerY + 2, z)
rat:setSpawn(30)
rat:setCreature("Rat", 30, Direction.SOUTH)

-- Autoborder
for x = centerX - 2, centerX + 2 do
    for y = centerY - 2, centerY + 2 do
        local b = map:getOrCreateTile(x, y, z)
        b:borderize()
    end
end