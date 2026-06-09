from typing import List


class DensityController:
    LEVELS = ["Low", "Medium", "High", "Extreme"]

    def choose_density(self, min_level: int, max_level: int) -> str:
        if max_level >= 500:
            return "Extreme"
        if max_level >= 400:
            return "High"
        if max_level >= 300:
            return "Medium"
        return "Low"

    def distribute_monsters(self, monster_list: List[str], density: str) -> List[str]:
        if density == "Extreme":
            return monster_list * 3
        if density == "High":
            return monster_list * 2
        if density == "Medium":
            return monster_list + monster_list[:2]
        return monster_list[:3]
