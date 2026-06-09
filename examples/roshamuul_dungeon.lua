if not app.hasMap() then
  return
end

app.transaction(function(map)
  local z = 7
  local function tileAt(x, y, z)
    return map:getOrCreateTile(x, y, z)
  end

  -- Cave entrance
  for x = 80, 94 do
    for y = 80, 94 do
      tileAt(x, y, z).ground = 1053
    end
  end
  tileAt(87, 87, z):setCreature("Nightmare", 120, Direction.SOUTH)
  tileAt(85, 85, z):setSpawn(3)

  -- Main cavern
  for x = 96, 118 do
    for y = 86, 110 do
      tileAt(x, y, z).ground = 1056
    end
  end
  tileAt(107, 98, z):setCreature("Demon", 120, Direction.SOUTH)
  tileAt(104, 96, z):addItem(2150)

  -- Secret alcove
  for x = 120, 124 do
    for y = 100, 104 do
      tileAt(x, y, z).ground = 1057
    end
  end
  tileAt(122, 102, z):addItem(2151)
  tileAt(122, 103, z):setSpawn(2)
end)
