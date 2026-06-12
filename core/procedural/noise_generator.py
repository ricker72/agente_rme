def simplex_noise_script(
    origin_x: int,
    origin_y: int,
    width: int,
    height: int,
    z: int,
    floor_high: int,
    floor_low: int,
) -> str:
    return f"""-- Procedural noise terrain generator
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
            if value > 0.1 then
                tile.ground = {floor_high}
            else
                tile.ground = {floor_low}
            end
        end
    end
end)
"""
