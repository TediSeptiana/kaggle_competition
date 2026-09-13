"""Main Agent logic for Kaggriculture with dynamic cascading priority execution."""

from typing import Any, Dict, List, Optional, Tuple
from pathfinding import get_closest_target, get_next_step


class DynamicFarmAgent:
    """Agent orchestrating farmer and farm hands with dynamic fallback priorities."""

    def __init__(self, max_coops: int = 5) -> None:
        self.max_coops = max_coops

    def evaluate_farm_state(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts and parses relevant metrics from game observation."""
        player = obs["player"]
        farm = obs["farms"][player]
        private = obs.get("private", {}) or {}

        tiles = farm["tiles"]
        board_size = len(tiles)

        coop_count = 0
        plant_tiles: List[Tuple[int, int]] = []
        unwatered_plants: List[Tuple[int, int]] = []
        harvestable_plants: List[Tuple[int, int]] = []
        empty_tiles: List[Tuple[int, int]] = []
        unfertilized_plants: List[Tuple[int, int]] = []

        for y in range(board_size):
            for x in range(board_size):
                tile = tiles[y][x]
                if tile == "LOCKED":
                    continue
                if tile is None:
                    empty_tiles.append((x, y))
                elif isinstance(tile, dict):
                    kind = tile.get("kind")
                    if kind == "COOP":
                        coop_count += 1
                    elif kind == "PLANT":
                        plant_tiles.append((x, y))
                        if tile.get("yield_units", 0) > 0:
                            harvestable_plants.append((x, y))
                        if not tile.get("watered_today", False):
                            unwatered_plants.append((x, y))
                        if tile.get("fertilized_until_day", -1) < obs.get("day", 0):
                            unfertilized_plants.append((x, y))

        return {
            "coop_count": coop_count,
            "harvestable": harvestable_plants,
            "unwatered": unwatered_plants,
            "unfertilized": unfertilized_plants,
            "empty_tiles": empty_tiles,
            "seeds": private.get("seeds", {}),
            "shed": private.get("shed", {}),
            "money": farm["money"],
            "farmer_pos": tuple(farm["farmer"]),
            "board_size": board_size,
        }

    def execute_cascading_priority(
        self, state: Dict[str, Any], priority_chain: List[str]
    ) -> List[Any]:
        """Executes actions based on a strict priority chain with fallback logic.

        Supported Priorities in order:
        - "BUILD_COOP": Build coop up to self.max_coops limit
        - "HARVEST": Harvest any ready crops
        - "PLANT": Plant seeds if available in inventory/seeds
        - "WATER": Water crops needing daily care
        - "FERTILIZE": Apply fertilizer if available
        - "PASS": Do nothing if no actions available
        """
        fx, fy = state["farmer_pos"]
        board_size = state["board_size"]
        seeds = state["seeds"]

        for priority in priority_chain:
            # Priority 1: BUILD COOP (with quota check)
            if priority == "BUILD_COOP":
                if state["coop_count"] < self.max_coops and state["empty_tiles"]:
                    target = state["empty_tiles"][0]
                    if (fx, fy) == target:
                        return ["BUILD_COOP"]
                    step = get_next_step((fx, fy), target, board_size)
                    if step:
                        return [step]

            # Priority 2: HARVEST
            elif priority == "HARVEST":
                if state["harvestable"]:
                    if (fx, fy) in state["harvestable"]:
                        return ["HARVEST"]
                    res = get_closest_target((fx, fy), state["harvestable"], board_size)
                    if res:
                        return [res[1]]

            # Priority 3: PLANT (Checks seed availability)
            elif priority == "PLANT":
                available_crops = [crop for crop, count in seeds.items() if count > 0]
                if available_crops and state["empty_tiles"]:
                    selected_crop = available_crops[0]
                    if (fx, fy) in state["empty_tiles"]:
                        return ["PLANT", selected_crop]
                    res = get_closest_target((fx, fy), state["empty_tiles"], board_size)
                    if res:
                        return [res[1]]

            # Priority 4: WATER
            elif priority == "WATER":
                if state["unwatered"]:
                    if (fx, fy) in state["unwatered"]:
                        return ["WATER"]
                    res = get_closest_target((fx, fy), state["unwatered"], board_size)
                    if res:
                        return [res[1]]

            # Priority 5: FERTILIZE
            elif priority == "FERTILIZE":
                if state["shed"].get("FERTILIZER", 0) > 0 and state["unfertilized"]:
                    if (fx, fy) in state["unfertilized"]:
                        return ["FERTILIZE"]
                    res = get_closest_target((fx, fy), state["unfertilized"], board_size)
                    if res:
                        return [res[1]]

        return ["PASS"]


# Agent entry point for Kaggle Environment
agent_instance = DynamicFarmAgent(max_coops=5)


def agent(obs: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Top-level agent function adhering to Kaggriculture specification."""
    state = agent_instance.evaluate_farm_state(obs)

    # Define strict priority sequence
    priority_sequence = ["BUILD_COOP", "HARVEST", "PLANT", "WATER", "FERTILIZE"]

    # Compute action for primary farmer
    farmer_action = agent_instance.execute_cascading_priority(state, priority_sequence)

    # Simple Market Logic: Buy Seeds if short on crops and money is available
    market_orders = []
    if state["money"] >= 80 and sum(state["seeds"].values()) == 0:
        market_orders.append(["BUY_SEED", "MELON", 1])

    return {"farmer": farmer_action, "hands": [], "market": market_orders}
"""
[cite: 1]
"""