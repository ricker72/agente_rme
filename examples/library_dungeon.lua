if not app.hasMap() then
  return
end

app.transaction(function(map)
  local z = 7
  local function tileAt(x, y, z)
    return map:getOrCreateTile(x, y, z)
  end

  -- Library halls
  for x = 98, 114 do
    for y = 90, 106 do
      tileAt(x, y, z).ground = 393
    end
  end
  tileAt(104, 98, z):setCreature("Warlock", 120, Direction.SOUTH)
  tileAt(100, 100, z):setSpawn(3)

  -- Boss gallery
  for x = 106, 118 do
    for y = 108, 118 do
      tileAt(x, y, z).ground = 415
    end
  end
  tileAt(112, 112, z):setCreature("Sphinx", 120, Direction.SOUTH)
  tileAt(110, 110, z):addItem(2148)

  -- Puzzle chamber
  for x = 92, 96 do
    for y = 112, 116 do
      tileAt(x, y, z).ground = 416
    end
  end
  tileAt(94, 114, z):addItem(2150)
end)
