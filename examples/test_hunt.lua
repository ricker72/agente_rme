if not app.hasMap() then
    return
end

local map = app.map

app.transaction()

local originX = 1040
local originY = 1000
local z = 7

-- Mini hunt zone 15x15 para nivel 300+
for x = originX, originX + 14 do
    for y = originY, originY + 14 do
        local tile = map:getOrCreateTile(x, y, z)
        tile.ground = 415
    end
end

-- Paredes exteriores
for x = originX, originX + 14 do
    local n = map:getOrCreateTile(x, originY, z)
    local s = map:getOrCreateTile(x, originY + 14, z)
    n:addItem(1495)
    s:addItem(1495)
end

for y = originY, originY + 14 do
    local w = map:getOrCreateTile(originX, y, z)
    local e = map:getOrCreateTile(originX + 14, y, z)
    w:addItem(1495)
    e:addItem(1495)
end

-- Habitaciones internas (conectadas por pasillos)
local rooms = {
    {x = originX + 2, y = originY + 2, w = 5, h = 4},
    {x = originX + 9, y = originY + 2, w = 4, h = 5},
    {x = originX + 2, y = originY + 9, w = 5, h = 4},
    {x = originX + 9, y = originY + 9, w = 4, h = 4},
}

for _, room in ipairs(rooms) do
    for rx = room.x, room.x + room.w do
        for ry = room.y, room.y + room.h do
            local t = map:getOrCreateTile(rx, ry, z)
            t.ground = 406
        end
    end
end

-- Spawns en cada habitación
local spawns = {
    {x = originX + 4, y = originY + 4, monster = "Sphinx", interval = 60},
    {x = originX + 11, y = originY + 4, monster = "Frazzlemaw", interval = 60},
    {x = originX + 4, y = originY + 11, monster = "Cloak Of Terror", interval = 90},
    {x = originX + 11, y = originY + 11, monster = "Vexclaw", interval = 120},
}

for _, s in ipairs(spawns) do
    local sp = map:getOrCreateTile(s.x, s.y, z)
    sp:setSpawn(s.interval)
    sp:setCreature(s.monster, s.interval, Direction.SOUTH)
end

-- Boss central
local boss = map:getOrCreateTile(originX + 7, originY + 7, z)
boss:setSpawn(600)
boss:setCreature("Crypt Warden", 600, Direction.SOUTH)

-- Decoración
local deco = map:getOrCreateTile(originX + 7, originY + 2, z)
deco:addItem(1700)

-- Autoborder
for x = originX, originX + 14 do
    for y = originY, originY + 14 do
        local b = map:getOrCreateTile(x, y, z)
        b:borderize()
    end
end