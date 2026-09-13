"""Kaggriculture Autonomous Agent (Day 0 - Day 29 / 720 Turns).

Uses dynamic state machine logic, pathfinding, and automated market execution.
"""

from typing import Any, Dict, List, Tuple
from pathfinding import get_next_step, extract_blocked_from_tiles
from market import MarketManager

# Farm Layout Configurations (NW Quadrant: 5x5)
COOP_TILES: List[Tuple[int, int]] = [(4, 0), (3, 0), (2, 0), (1, 0), (0, 0)]
WHEAT_TILES: List[Tuple[int, int]] = [(0, 3), (1, 3), (2, 3), (3, 3), (4, 3)]
SHED_TILES: List[Tuple[int, int]] = [(4, 4), (5, 4), (4, 5), (5, 5)]


def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Master entry point for Kaggle Environments."""
    step: int = obs.get("step")
    if step is None:
        step = obs.get("day", 0) * 24 + obs.get("hour", 0)

    day: int = obs.get("day", step // 24)
    hour: int = obs.get("hour", step % 24)
    player: int = obs.get("player", 0)
    farms: List[Dict[str, Any]] = obs.get("farms", [])
    private: Dict[str, Any] = obs.get("private", {}) or {}

    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    my_farm = farms[player]
    fx, fy = my_farm.get("farmer", [4, 4])
    hired_hands = my_farm.get("hands", [])
    tiles = my_farm.get("tiles", [])

    # Extract current obstacles
    blocked = extract_blocked_from_tiles(tiles, allow_locked_pass=True)

    # 1. Process Market Orders
    market_orders = MarketManager.get_market_orders(obs, my_farm, private)

    # 2. Process Farmer Action
    farmer_action: List[str] = ["PASS"]

    if day == 0:
        # --- DAY 0 INITIALIZATION BOOTSTRAP ---
        if hour < 4:
            # Move towards coop row y=0
            step_dir = get_next_step((fx, fy), COOP_TILES[0], blocked=blocked)
            farmer_action = [step_dir]
        elif 4 <= hour <= 12:
            idx = (hour - 4) // 2
            if idx < len(COOP_TILES):
                target = COOP_TILES[idx]
                if (fx, fy) != target:
                    farmer_action = [get_next_step((fx, fy), target, blocked=blocked)]
                else:
                    farmer_action = ["BUILD_COOP"]
        elif hour > 12:
            target_wheat = WHEAT_TILES[min(hour - 13, len(WHEAT_TILES) - 1)]
            if (fx, fy) != target_wheat:
                farmer_action = [get_next_step((fx, fy), target_wheat, blocked=blocked)]
            else:
                current_tile = tiles[fy][fx]
                if current_tile is None and private.get("seeds", {}).get("WHEAT", 0) > 0:
                    farmer_action = ["PLANT", "WHEAT"]
                elif isinstance(current_tile, dict) and not current_tile.get("watered_today", False):
                    farmer_action = ["WATER"]
    else:
        # --- DAY 1 TO 29 RECURRING ROUTINE ---
        # Morning routine (Hours 0-11): Care for Geese & Collect Fertilizer
        if hour < 10:
            coop_idx = min(hour // 2, len(COOP_TILES) - 1)
            target_coop = COOP_TILES[coop_idx]
            if (fx, fy) != target_coop:
                farmer_action = [get_next_step((fx, fy), target_coop, blocked=blocked)]
            else:
                tile = tiles[fy][fx]
                if isinstance(tile, dict) and tile.get("kind") == "COOP":
                    if not tile.get("fed_today", False):
                        farmer_action = ["FEED"]
                    elif tile.get("fertilizer_available", False):
                        farmer_action = ["COLLECT_FERTILIZER"]
                    elif tile.get("yield_units", 0) > 0:
                        farmer_action = ["HARVEST"]

        # Afternoon routine (Hours 12-23): Manage Crop Fields
        else:
            wheat_idx = (hour - 10) % len(WHEAT_TILES)
            target_wheat = WHEAT_TILES[wheat_idx]
            if (fx, fy) != target_wheat:
                farmer_action = [get_next_step((fx, fy), target_wheat, blocked=blocked)]
            else:
                tile = tiles[fy][fx]
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    crop_age = day - tile.get("planted_day", day)
                    if crop_age >= 2 and tile.get("yield_units", 0) > 0:
                        farmer_action = ["HARVEST"]
                    elif not tile.get("watered_today", False):
                        farmer_action = ["WATER"]
                elif tile is None and private.get("seeds", {}).get("WHEAT", 0) > 0:
                    farmer_action = ["PLANT", "WHEAT"]

    # 3. Process Hired Hands Actions
    hands_actions: List[List[str]] = []
    if len(hired_hands) > 0:
        for hand_idx, hand_pos in enumerate(hired_hands):
            hx, hy = hand_pos
            hand_act = ["PASS"]

            if day == 0:
                # Day 0: Assist in placing geese in newly built coops
                if hour == 1:
                    hand_act = ["PICKUP", "GOOSE", 5]
                else:
                    coop_target = COOP_TILES[min(hour // 2, len(COOP_TILES) - 1)]
                    if (hx, hy) != coop_target:
                        hand_act = [get_next_step((hx, hy), coop_target, blocked=blocked)]
                    else:
                        hand_act = ["PLACE", "GOOSE"]
            else:
                # Day 1+: Assist in watering/harvesting crops
                target_crop = WHEAT_TILES[(hour + hand_idx) % len(WHEAT_TILES)]
                if (hx, hy) != target_crop:
                    hand_act = [get_next_step((hx, hy), target_crop, blocked=blocked)]
                else:
                    tile = tiles[hy][hx]
                    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                        if not tile.get("watered_today", False):
                            hand_act = ["WATER"]
                        elif tile.get("yield_units", 0) > 0:
                            hand_act = ["HARVEST"]

            hands_actions.append(hand_act)

    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market_orders,
    }


# ==========================================
# Local Validation & Simulation Runner
# ==========================================
if __name__ == "__main__":
    from kaggle_environments import make

    print("Running 720-step Full Game Validation...")
    env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
    env.run([agent, "random"])

    final_step = env.steps[-1]
    for p_idx, player_state in enumerate(final_step):
        print(f"Player {p_idx} Final Score: {player_state.reward} | Status: {player_state.status}")