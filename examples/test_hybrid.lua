if not app.hasMap() then
    return
end

local map = app.map

app.transaction()

-- Issavi zone (arena, templos brillantes)
local issaviX = 1000
local issaviY = 1050
local z = 7

for x = issaviX, issaviX + 9 do
    for y = issaviY, issaviY + 9 do
        local tile = map:getOrCreateTile(x, y, z)
        tile.ground = 817
    end
end

for x = issaviX, issaviX + 9 do
    local n = map:getOrCreateTile(x, issaviY, z)
    local s = map:getOrCreateTile(x, issaviY + 9, z)
    n:addItem(1495)
    s:addItem(1495)
end

for y = issaviY, issaviY + 9 do
    local w = map:getOrCreateTile(issaviX, y, z)
    local e = map:getOrCreateTile(issaviX + 9, y, z)
    w:addItem(1495)
    e:addItem(1495)
end

local issaviSpawn = map:getOrCreateTile(issaviX + 4, issaviY + 4, z)
issaviSpawn:setSpawn(60)
issaviSpawn:setCreature("Crypt Warden", 60, Direction.SOUTH)

-- Roshamuul zone (roca, sombras)
local roshX = 1020
local roshY = 1050

for x = roshX, roshX + 9 do
    for y = roshY, roshY + 9 do
        local tile = map:getOrCreateTile(x, y, z)
        tile.ground = 395
    end
end

for x = roshX, roshX + 9 do
    local n = map:getOrCreateTile(x, roshY, z)
    local s = map:getOrCreateTile(x, roshY + 9, z)
    n:addItem(1497)
    s:addItem(1497)
end

for y = roshY, roshY + 9 do
    local w = map:getOrCreateTile(roshX, y, z)
    local e = map:getOrCreateTile(roshX + 9, y, z)
    w:addItem(1497)
    e:addItem(1497)
end

local roshSpawn = map:getOrCreateTile(roshX + 5, roshY + 5, z)
roshSpawn:setSpawn(60)
roshSpawn:setCreature("Frazzlemaw", 60, Direction.SOUTH)

-- Corredor de conexión entre Issavi y Roshamuul
for cx = issaviX + 10, roshX - 1 do
    local corridor = map:getOrCreateTile(cx, issaviY + 4, z)
    corridor.ground = 406
end

-- Decoración híbrida (alfombras + rocas)
local cross1 = map:getOrCreateTile(issaviX + 7, issaviY + 7, z)
cross1:addItem(1700)

local cross2 = map:getOrCreateTile(roshX + 2, roshY + 7, z)
cross2:addItem(1702)

-- Autoborder en ambas zonas
for x = issaviX, issaviX + 9 do
    for y = issaviY, issaviY + 9 do
        local b = map:getOrCreateTile(x, y, z)
        b:borderize()
    end
end

for x = roshX, roshX + 9 do
    for y = roshY, roshY + 9 do
        local b = map:getOrCreateTile(x, y, z)
        b:borderize()
    end
end