if not app.hasMap() then
  return
end

app.transaction(function(map)
  local z = 7
  local function tileAt(x, y, z)
    return map:getOrCreateTile(x, y, z)
  end

  -- Entrance hall
  for x = 90, 104 do
    for y = 90, 104 do
      tileAt(x, y, z).ground = 415
    end
  end
  tileAt(97, 92, z):setCreature("Hydra", 120, Direction.SOUTH)
  tileAt(97, 93, z):setSpawn(3)

  -- Boss chamber
  for x = 110, 120 do
    for y = 90, 100 do
      tileAt(x, y, z).ground = 393
    end
  end
  tileAt(115, 95, z):setCreature("Dragon", 120, Direction.SOUTH)
  tileAt(113, 94, z):addItem(2153)

  -- Connection corridor
  for x = 105, 109 do
    tileAt(x, 97, z).ground = 415
    tileAt(x, 97, z):borderize()
  end

  -- Treasure room
  for x = 88, 92 do
    for y = 110, 114 do
      tileAt(x, y, z).ground = 416
    end
  end
  tileAt(90, 112, z):addItem(2150)
  tileAt(92, 112, z):setSpawn(2)
end)
