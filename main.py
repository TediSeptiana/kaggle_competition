"""Kaggriculture Agent — priority-driven, di-drive oleh pathfinding + market.

PRIORITAS (tinggi → rendah):
  1. HARVEST          (semua unit harvest dulu kalau ada hasil)
  2. BUILD_COOP       (farmer)
  3. PLACE_GOOSE      (hand)
  4. PLANT            (semua unit)
  5. COLLECT_FERT     (hand)
  6. FEED             (hand)
  7. FERTILIZE        (semua unit)
  8. WATER            (semua unit)
"""

from typing import Any, Dict, List, Optional, Tuple

from pathfinding import (
    get_route_actions, extract_blocked_from_tiles, sort_by_distance,
    find_build_tiles, find_plant_tiles, find_harvest_tiles,
    find_place_goose_tiles, find_collect_fertilizer_tiles,
    find_feed_tiles, find_water_tiles, find_fertilize_tiles,
)
from market import decide_market_orders


# =====================================================================
# CONFIG — semua angka bisa diedit di sini
# =====================================================================
CONFIG = {
    # Setup day 0
    "BUY_GOOSE": 5,
    "BUY_WHEAT_SEED": 5,
    "BUY_FERTILIZER": 5,
    "BUY_WHEAT_FEED": 15,

    # Target kapasitas
    "COOP_TARGET": 5,
    "WHEAT_TARGET": 5,

    # Cycle
    "WHEAT_CYCLE_DAYS": 3,

    # Daily market
    "DAILY_BUY_WHEAT_FEED": 5,
    "HIRE_HAND": True,

    # Market — hold vs sell
    "KEEP_FERTILIZER": 10,
    "WHEAT_SHED_BUFFER": 10,

    # Layout (NW quadrant)
    "COOP_ROW": 0,
    "WHEAT_ROW": 3,

    # Grid
    "GRID_W": 10,
    "GRID_H": 10,
    "TURNS_PER_DAY": 24,
}


# =====================================================================
# PRIORITAS
# =====================================================================
PRIORITY_ORDER = [
    "HARVEST",
    "BUILD_COOP",
    "PLACE_GOOSE",
    "PLANT",
    "COLLECT_FERTILIZER",
    "FEED",
    "FERTILIZE",
    "WATER",
]

ACTION_FOR_PRIORITY = {
    "HARVEST": ["HARVEST"],
    "BUILD_COOP": ["BUILD_COOP"],
    "PLACE_GOOSE": ["PLACE", "GOOSE"],
    "PLANT": ["PLANT", "WHEAT"],
    "COLLECT_FERTILIZER": ["COLLECT_FERTILIZER"],
    "FEED": ["FEED"],
    "FERTILIZE": ["FERTILIZE"],
    "WATER": ["WATER"],
}

FARMER_WHITELIST = {"HARVEST", "BUILD_COOP", "PLANT", "FERTILIZE", "WATER"}
HAND_WHITELIST   = {"HARVEST", "PLACE_GOOSE", "COLLECT_FERTILIZER",
                    "FEED", "PLANT", "WATER", "FERTILIZE"}


# =====================================================================
# SCAN TASK  (FIXED: kirim current_day)
# =====================================================================
def scan_tasks(tiles, config, current_day):
    return {
        "HARVEST":             find_harvest_tiles(tiles, current_day),
        "BUILD_COOP":          find_build_tiles(
                                    tiles, config["COOP_TARGET"],
                                    row=config["COOP_ROW"],
                                    origin=(4, 4)),
        "PLACE_GOOSE":         find_place_goose_tiles(tiles),
        "PLANT":               find_plant_tiles(
                                    tiles, config["WHEAT_TARGET"],
                                    row=config["WHEAT_ROW"],
                                    origin=(4, 4)),
        "COLLECT_FERTILIZER":  find_collect_fertilizer_tiles(tiles),
        "FEED":                find_feed_tiles(tiles),
        "FERTILIZE":           find_fertilize_tiles(tiles),
        "WATER":               find_water_tiles(tiles),
    }


def pick_task(tasks, origin, whitelist):
    """Return (priority, target_tile, action) atau None."""
    for p in PRIORITY_ORDER:
        if p not in whitelist:
            continue
        tiles = tasks.get(p)
        if not tiles:
            continue
        target = sort_by_distance(tiles, origin)[0]
        return p, target, ACTION_FOR_PRIORITY[p]
    return None


# =====================================================================
# AGENT
# =====================================================================
def agent(obs: Dict[str, Any]) -> Dict[str, Any]:
    step = obs.get("step")
    if step is None:
        step = obs["day"] * 24 + obs["hour"]

    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    me = farms[player]
    farmer_pos = tuple(me["farmer"])
    hands = me.get("hands", [])
    tiles = me["tiles"]
    blocked = extract_blocked_from_tiles(tiles)

    market_orders = decide_market_orders(obs, CONFIG)

    # FIXED: kirim current_day
    current_day = obs["day"]
    tasks = scan_tasks(tiles, CONFIG, current_day)

    # ---------- FARMER ----------
    farmer_action = ["PASS"]
    pick = pick_task(tasks, farmer_pos, FARMER_WHITELIST)
    if pick is not None:
        _, target, action = pick
        if farmer_pos == target:
            farmer_action = action
        else:
            route = get_route_actions(farmer_pos, target,
                                      width=CONFIG["GRID_W"],
                                      height=CONFIG["GRID_H"],
                                      blocked=blocked)
            farmer_action = [route[0]] if route else ["PASS"]

    # ---------- HANDS ----------
    hands_actions: List[List[str]] = []
    for hand in hands:
        hpos = tuple(hand)
        pick_h = pick_task(tasks, hpos, HAND_WHITELIST)
        if pick_h is None:
            hands_actions.append(["PASS"])
            continue
        _, target, action = pick_h
        if hpos == target:
            hands_actions.append(action)
        else:
            route = get_route_actions(hpos, target,
                                      width=CONFIG["GRID_W"],
                                      height=CONFIG["GRID_H"],
                                      blocked=blocked)
            hands_actions.append([route[0]] if route else ["PASS"])

    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market_orders,
    }


# =====================================================================
# TEST
# =====================================================================
if __name__ == "__main__":
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
    env.run([agent, "random"])
    for i, s in enumerate(env.steps[-1]):
        print(f"Player {i}: reward={s.reward} | status={s.status}")