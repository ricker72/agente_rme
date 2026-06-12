"""Quick smoke test of the Visual Map Critic AI."""

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.region import Region
from core.world.structure import Structure
from core.world.spawn import Spawn
from core.critic import VisualCritic

w = WorldModel()
# 20x20 ground floor with items on every 3rd tile
for x in range(20):
    for y in range(20):
        items = [{"itemid": 200 + (x + y) % 5, "count": 1}] if (x + y) % 3 == 0 else []
        w.set_tile(Tile(x=x, y=y, z=7, ground=100, items=items))
# spawns in the middle
for x, y in [(5, 5), (6, 5), (7, 5), (8, 5), (9, 5)]:
    t = w.get_tile(x, y, 7)
    if t:
        t.spawn = Spawn(monster="Dragon", respawn=60, radius=3)
        t.zone = "hunt_north"
# hunt zone and city services
w.add_region(Region(name="hunt_north", theme="issavi", min_level=300, max_level=400))
w.add_region(Region(name="city_issavi", theme="issavi", min_level=1, max_level=200))
w.add_region(Region(name="city_issavi_depot", theme="issavi"))
w.add_region(Region(name="city_issavi_temple", theme="issavi"))
# boss structure
w.add_structure(
    Structure(
        name="boss_arena",
        category="boss_room",
        x=15,
        y=15,
        z=7,
        width=10,
        height=10,
        tags=["boss"],
    )
)

critic = VisualCritic()
result = critic.analyze(
    w, map_name="test_issavi", output_dir="output/critic_test", generate_heatmaps=True
)
print("overall:", round(result.overall_score, 2))
print("visual:", round(result.visual_score, 2))
print("nav:", round(result.navigation_score, 2))
print("density:", round(result.density_score, 2))
print("spawn:", round(result.spawn_score, 2))
print("hunt:", round(result.hunt_score, 2))
print("boss:", round(result.boss_score, 2))
print("city:", round(result.city_score, 2))
print("decor:", round(result.decor_score, 2))
print("pathfinding:", round(result.pathfinding_score, 2))
print("issues:", len(result.issues), "recs:", len(result.recommendations))
for art, p in (result.metadata.get("artifacts") or {}).items():
    print("  artifact", art, "->", p)
