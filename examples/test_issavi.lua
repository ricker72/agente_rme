if not app.hasMap() then
    return
end

local map = app.map

app.transaction()

local originX = 1000
local originY = 1000
local z = 7

-- Suelo desierto Issavi (ground 817 = arena)
for x = originX, originX + 9 do
    for y = originY, originY + 9 do
        local tile = map:getOrCreateTile(x, y, z)
        tile.ground = 817
    end
end

-- Muros de piedra alrededor
for x = originX, originX + 9 do
    local wallN = map:getOrCreateTile(x, originY, z)
    local wallS = map:getOrCreateTile(x, originY + 9, z)
    wallN:addItem(1495)
    wallS:addItem(1495)
end

for y = originY, originY + 9 do
    local wallW = map:getOrCreateTile(originX, y, z)
    local wallE = map:getOrCreateTile(originX + 9, y, z)
    wallW:addItem(1495)
    wallE:addItem(1495)
end

-- Decoración Issavi (alfombras, jarrones)
local carpet = map:getOrCreateTile(originX + 4, originY + 4, z)
carpet:addItem(1700)

local vase1 = map:getOrCreateTile(originX + 2, originY + 7, z)
vase1:addItem(1701)

local vase2 = map:getOrCreateTile(originX + 7, originY + 2, z)
vase2:addItem(1701)

-- Spawn de Crypt Warden
local spawn1 = map:getOrCreateTile(originX + 5, originY + 5, z)
spawn1:setSpawn(60)
spawn1:setCreature("Crypt Warden", 60, Direction.SOUTH)

-- Autoborder
for x = originX, originX + 9 do
    for y = originY, originY + 9 do
        local b = map:getOrCreateTile(x, y, z)
        b:borderize()
    end
end