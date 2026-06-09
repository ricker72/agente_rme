from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .floor_generator import Floor


class CaveGenerator:
    def carve_cave(self, floor: "Floor", fill_threshold: int = 46, iterations: int = 4) -> None:
        width = floor.width
        height = floor.height
        grid = [[1 if x == 0 or y == 0 or x == width - 1 or y == height - 1 else 0 for x in range(width)] for y in range(height)]
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                grid[y][x] = 1 if (x + y) % 2 == 0 else 0

        for _ in range(iterations):
            grid = self._step(grid, width, height, fill_threshold)

        floor.cave_tiles = []
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 0:
                    floor.cave_tiles.append((x, y))

    def _step(self, grid, width, height, threshold):
        new_grid = [[grid[y][x] for x in range(width)] for y in range(height)]
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                wall_count = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if grid[y + dy][x + dx] == 1:
                            wall_count += 1
                new_grid[y][x] = 1 if wall_count > threshold else 0
        return new_grid
