# OpenTibiaBR RME API Reference

## app

- `app.hasMap()`
  - Devuelve `true` si existe un mapa cargado en RME.

- `app.map`
  - Referencia al mapa actualmente cargado.

- `app.transaction(function(map) ... end)`
  - Ejecuta los cambios en un bloque transaccional.
  - Cualquier modificación de tiles o entidades debe hacerse dentro de este bloque.

- `app.setCameraPosition(x, y, z)`
  - Cambia la cámara a una posición específica del mapa.

## map

- `map:getOrCreateTile(x, y, z)`
  - Obtiene un tile existente o crea uno nuevo en la coordenada indicada.

## tile

- `tile.ground = itemId`
  - Establece el terreno del tile a un ID de item válido.

- `tile:addItem(itemId)`
  - Añade un objeto encima del tile.

- `tile:borderize()`
  - Crea un borde alrededor del tile para definir áreas o contornos.

- `tile:setSpawn(radius)`
  - Define un punto de spawn para criaturas en el tile, con radio opcional.

- `tile:setCreature(monsterName, spawnTime, Direction.SOUTH)`
  - Coloca un spawn de criatura en el tile con dirección y tiempo de reaparición.

## geo

- `geo.randomScatter(x, y, density)`
  - Genera una dispersión aleatoria en coordenadas.
  - Se puede usar para colocar objetos decorativos o recursos de forma natural.

## noise

- `noise.simplex(x, y, z)`
  - Genera ruido simplex para crear terreno procedural: cuevas, formas de terreno y variación natural.

## Dialog

- `Dialog()`
  - Crea interfaces de interacción en RME.

### Métodos frecuentes de Dialog

- `Dialog():label(text)`
  - Añade una etiqueta de texto.

- `Dialog():input(label, default)`
  - Añade un campo de texto para entrada de usuario.

- `Dialog():check(label, default)`
  - Añade una casilla de verificación.

- `Dialog():number(label, default)`
  - Añade un campo numérico.

- `Dialog():button(label, callback)`
  - Añade un botón con callback.

- `Dialog():show()`
  - Muestra la ventana de diálogo.

## Ejemplos funcionales

### Generar un tile de terreno

```lua
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local tile = map:getOrCreateTile(100, 100, 7)
    tile.ground = 415
end)
```

### Añadir un objeto decorativo

```lua
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local tile = map:getOrCreateTile(101, 100, 7)
    tile:addItem(2148)
end)
```

### Configurar un spawn de criatura

```lua
if not app.hasMap() then
    return
end

app.transaction(function(map)
    local tile = map:getOrCreateTile(105, 105, 7)
    tile:setCreature("Frazzlemaw", 30000, Direction.SOUTH)
end)
```

### Crear un camino simple

```lua
if not app.hasMap() then
    return
end

app.transaction(function(map)
    for x = 110, 118 do
        local tile = map:getOrCreateTile(x, 120, 7)
        tile.ground = 415
    end
end)
```

### Usar ruido simplex

```lua
if not app.hasMap() then
    return
end

app.transaction(function(map)
    for x = 100, 110 do
        for y = 100, 110 do
            local value = noise.simplex(x * 0.15, y * 0.15, 0)
            local tile = map:getOrCreateTile(x, y, 7)
            if value > 0.1 then
                tile.ground = 393
            else
                tile.ground = 415
            end
        end
    end
end)
```
