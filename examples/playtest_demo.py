"""Playtest Engine Demo — generates a real playtest report."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.playtest.playtest_engine import PlaytestEngine
from core.playtest.report_generator import ReportGenerator

# Build a 30x30 hunt world with spawns
world = WorldModel()
world.regions.append(Region(name="issavi_hunt"))

monsters = ["Dragon", "Hydra", "Demon", "Vampire", "Behemoth"]
idx = 0
for x in range(30):
    for y in range(30):
        tile = Tile(x=x, y=y, z=7, ground=100)
        if (x + y) % 5 == 0:
            tile.spawn = Spawn(monster=monsters[idx % len(monsters)])
            idx += 1
        world.set_tile(tile)

# Run full playtest
engine = PlaytestEngine(seed=42, player_level=300)
report = engine.run(world)

# Print report
gen = ReportGenerator()
print(gen.format_summary(report))

# Save JSON
gen.save_report(report, "output/playtest_report.json")