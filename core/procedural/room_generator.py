def room_generator_lua(x1: int, y1: int, x2: int, y2: int, z: int, floor_id: int, wall_id: int) -> str:
    return f"""-- Room generator
if not app.hasMap() then
    return
end

app.transaction(function(map)
    for x = {x1}, {x2} do
        for y = {y1}, {y2} do
            local tile = map:getOrCreateTile(x, y, {z})
            if x == {x1} or x == {x2} or y == {y1} or y == {y2} then
                tile.ground = {wall_id}
            else
                tile.ground = {floor_id}
            end
        end
    end
end)
"""
