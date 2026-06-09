if not app.hasMap() then
    return
end

local map = app.map

app.transaction()

local originX = 1020
local originY = 1000
local z = 7

-- Suelo rocoso Roshamuul (ground 395 = roca)
for x = originX, originX + 9 do
    for y = originY, originY + 9 do
        local tile = map:getOrCreateTile(x, y, z)
        tile.ground = 395
    end
end

-- Paredes oscuras de Roshamuul
for x = originX, originX + 9 do
    local wallN = map:getOrCreateTile(x, originY, z)
    local wallS = map:getOrCreateTile(x, originY + 9, z)
    wallN:addItem(1497)
    wallS:addItem(1497)
end

for y = originY, originY + 9 do
    local wallW = map:getOrCreateTile(originX, y, z)
    local wallE = map:getOrCreateTile(originX + 9, y, z)
    wallW:addItem(1497)
    wallE:addItem(1497)
end

-- Decoración Roshamuul (rocas, huesos)
local rock1 = map:getOrCreateTile(originX + 2, originY + 2, z)
rock1:addItem(1702)

local bone = map:getOrCreateTile(originX + 7, originY + 8, z)
bone:addItem(1703)

local rock2 = map:getOrCreateTile(originX + 8, originY + 3, z)
rock2:addItem(1702)

-- Spawn de Frazzlemaw
local spawn1 = map:getOrCreateTile(originX + 5, originY + 5, z)
spawn1:setSpawn(60)
spawn1:setCreature("Frazzlemaw", 60, Direction.SOUTH)

-- Spawn de Vexclaw
local spawn2 = map:getOrCreateTile(originX + 3, originY + 7, z)
spawn2:setSpawn(120)
spawn2:setCreature("Vexclaw", 120, Direction.SOUTH)

-- Autoborder
for x = originX, originX + 9 do
    for y = originY, originY + 9 do
        local b = map:getOrCreateTile(x, y, z)
        b:borderize()
    end
end