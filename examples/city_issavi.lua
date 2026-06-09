if not app.hasMap() then
  return
end

app.transaction(function(map)
  local z = 7
  local function tileAt(x, y)
    return map:getOrCreateTile(x, y, z)
  end

  local function fillArea(x, y, width, height, groundId)
    for ix = x, x + width - 1 do
      for iy = y, y + height - 1 do
        tileAt(ix, iy).ground = groundId
      end
    end
  end

  local function borderArea(x, y, width, height)
    for ix = x, x + width - 1 do
      tileAt(ix, y):borderize()
      tileAt(ix, y + height - 1):borderize()
    end
    for iy = y, y + height - 1 do
      tileAt(x, iy):borderize()
      tileAt(x + width - 1, iy):borderize()
    end
  end

  -- Plaza central
  fillArea(94, 94, 14, 14, 415)
  borderArea(94, 94, 14, 14)
  tileAt(100, 100):addItem(2153)
  tileAt(101, 100):addItem(2153)

  -- Temple Issavi
  fillArea(80, 80, 10, 10, 393)
  borderArea(80, 80, 10, 10)
  tileAt(85, 84):addItem(2150)
  tileAt(84, 86):addItem(2153)
  tileAt(85, 87):addItem(2153)
  tileAt(86, 85):addItem(1803)

  -- Depot sector
  fillArea(104, 76, 10, 8, 416)
  borderArea(104, 76, 10, 8)
  tileAt(107, 79):addItem(2150)
  tileAt(109, 81):addItem(2150)
  tileAt(106, 78):addItem(1803)

  -- Mercado
  fillArea(104, 98, 12, 10, 415)
  borderArea(104, 98, 12, 10)
  tileAt(107, 101):addItem(2151)
  tileAt(110, 101):addItem(2151)
  tileAt(107, 104):addItem(2151)

  -- Harbor
  fillArea(100, 118, 16, 10, 396)
  borderArea(100, 118, 16, 6)
  tileAt(106, 122):addItem(2149)
  tileAt(110, 122):addItem(2149)
  tileAt(107, 118):addItem(2155)

  -- Distrito residencial
  fillArea(76, 104, 16, 10, 416)
  borderArea(76, 104, 16, 10)
  tileAt(80, 108):addItem(1803)
  tileAt(83, 111):addItem(1803)
  tileAt(86, 109):addItem(2148)

  -- Caminos principales de acceso
  for x = 90, 104 do
    tileAt(x, 94).ground = 415
    tileAt(x, 94):borderize()
  end
  for y = 94, 118 do
    tileAt(104, y).ground = 415
    tileAt(104, y):borderize()
  end
end)
