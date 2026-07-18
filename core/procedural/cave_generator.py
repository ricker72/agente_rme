def cave_generator_lua(
    origin_x: int,
    origin_y: int,
    width: int,
    height: int,
    z: int,
    floor_id: int,
    wall_id: int,
) -> str:
    return """-- Cave generator using noise.simplex
if not app.hasMap() then
    return
end

app.transaction(function(map)
    for dx = 0, {width} - 1 do
        for dy = 0, {height} - 1 do
            local x = {origin_x} + dx
            local y = {origin_y} + dy
            local value = noise.simplex(x * 0.18, y * 0.18, 0)
            local tile = map:getOrCreateTile(x, y, {z})
            if value > 0.05 then
                tile.ground = {floor_id}
            else
                tile.ground = {wall_id}
            end
        end
    end
end)
"""
