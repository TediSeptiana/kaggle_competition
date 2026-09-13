"""Kaggriculture Agent — farmer-only, tile-list eksplisit.

Layout:
  Coop   : baris y=4, dari (4,4) ke (0,4)  → dekat shed, mundur ke barat
  Wheat  : baris y=3, dari (0,3) ke (2,3)  → 1 tile di atas coop
"""

from typing import Any, Dict, List, Tuple

from pathfinding import (
    get_route_actions, extract_blocked_from_tiles, sort_by_distance,
    find_harvest_tiles, find_water_tiles, find_feed_tiles,
    find_collect_fertilizer_tiles, find_fertilize_tiles,
    find_place_goose_tiles,
)
from market import decide_market_orders


# =====================================================================
# CONFIG — semua di sini
# =====================================================================
CONFIG = {
    "BUY_GOOSE": 5,
    "BUY_WHEAT_SEED": 5,
    "BUY_FERTILIZER": 5,
    "BUY_WHEAT_FEED": 15,

    "WHEAT_CYCLE_DAYS": 3,

    "DAILY_BUY_WHEAT_FEED": 5,
    "HIRE_HAND": False,          # ← MATIKAN karena kita farmer-only

    "KEEP_FERTILIZER": 10,
    "WHEAT_SHED_BUFFER": 10,

    "GRID_W": 10,
    "GRID_H": 10,
    "TURNS_PER_DAY": 24,
}

# ---------------------------------------------------------------------
# TILE LAYOUT — tinggal edit di sini
# ---------------------------------------------------------------------
# Urutan coop: dimulai dari yang paling dekat dengan shed (4,4),
# lalu mundur ke barat. Farmer spawn di (4,4) jadi langsung bisa build.
COOP_TILES: List[Tuple[int, int]] = [
    (4, 4),
    (3, 4),
    (2, 4),
    (1, 4),
    (0, 4),
]

# Wheat 1 tile di atas coop (y=3), dari barat ke timur
WHEAT_TILES: List[Tuple[int, int]] = [
    (0, 3),
    (1, 3),
    (2, 3),
    (3, 3),
    (4, 3),
]

SHED_ADJACENT = [(4, 4), (5, 4), (4, 5), (5, 5)]


# =====================================================================
# PRIORITAS
# =====================================================================
PRIORITY_ORDER = [
    "HARVEST",
    "BUILD_COOP",
    "PLACE_GOOSE",
    "PLANT",
    "FEED",
    "COLLECT_FERTILIZER",
    "FERTILIZE",
    "WATER",
]

ACTION_FOR_PRIORITY = {
    "HARVEST":            ["HARVEST"],
    "BUILD_COOP":         ["BUILD_COOP"],
    "PLACE_GOOSE":        ["PLACE", "GOOSE"],
    "PLANT":              ["PLANT", "WHEAT"],
    "FEED":               ["FEED"],
    "COLLECT_FERTILIZER": ["COLLECT_FERTILIZER"],
    "FERTILIZE":          ["FERTILIZE"],
    "WATER":              ["WATER"],
}

ACTION_NEEDS_ITEM = {
    "PLACE_GOOSE": "GOOSE",
    "FEED":        "WHEAT",
    "FERTILIZE":   "FERTILIZER",
}


# =====================================================================
# LOCATOR — pakai list eksplisit, bukan "farthest" dynamic
# =====================================================================
def tasks_build_coop(tiles):
    """Tile di COOP_TILES yang masih kosong (None)."""
    out = []
    for (x, y) in COOP_TILES:
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
            if tiles[y][x] is None:
                out.append((x, y))
    return out


def tasks_plant_wheat(tiles):
    """Tile di WHEAT_TILES yang masih kosong."""
    out = []
    for (x, y) in WHEAT_TILES:
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
            if tiles[y][x] is None:
                out.append((x, y))
    return out


def tasks_place_goose(tiles):
    """Coop kosong (belum ada goose) — hanya di COOP_TILES."""
    out = []
    for (x, y) in COOP_TILES:
        t = tiles[y][x]
        if isinstance(t, dict) and t.get("kind") == "COOP" \
           and t.get("animal") is None:
            out.append((x, y))
    return out


# =====================================================================
# SCAN TASK
# =====================================================================
def scan_tasks(tiles, current_day):
    return {
        "HARVEST":            find_harvest_tiles(tiles, current_day),
        "BUILD_COOP":         tasks_build_coop(tiles),
        "PLACE_GOOSE":        tasks_place_goose(tiles),
        "PLANT":              tasks_plant_wheat(tiles),
        "FEED":               find_feed_tiles(tiles),
        "COLLECT_FERTILIZER": find_collect_fertilizer_tiles(tiles),
        "FERTILIZE":          find_fertilize_tiles(tiles),
        "WATER":              find_water_tiles(tiles),
    }


# =====================================================================
# PICK TASK
# =====================================================================
def _get_inv(obs, idx=0):
    priv = obs.get("private", {}) or {}
    invs = priv.get("inventories", []) or []
    return invs[idx] if idx < len(invs) else {}


def _shed(obs, item):
    return (obs.get("private", {}) or {}).get("shed", {}).get(item, 0)


def pick_task(tasks, origin, inventory, obs):
    for p in PRIORITY_ORDER:
        tiles = tasks.get(p)
        if not tiles:
            continue

        # Auto-pickup: kalau butuh item tapi inventory kosong
        need = ACTION_NEEDS_ITEM.get(p)
        if need and inventory.get(need, 0) <= 0:
            if _shed(obs, need) <= 0:
                continue
            target = sort_by_distance(SHED_ADJACENT, origin)[0]
            qty = min(5, len(tiles))
            return p, target, ["PICKUP", need, qty]

        # Pilih target terdekat
        target = sort_by_distance(tiles, origin)[0]
        return p, target, ACTION_FOR_PRIORITY[p]
    return None


# =====================================================================
# AGENT
# =====================================================================
def agent(obs):
    step = obs.get("step")
    if step is None:
        step = obs["day"] * 24 + obs["hour"]

    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    me = farms[player]
    farmer_pos = tuple(me["farmer"])
    tiles = me["tiles"]
    blocked = extract_blocked_from_tiles(tiles)

    market_orders = decide_market_orders(obs, CONFIG)
    tasks = scan_tasks(tiles, obs["day"])

    farmer_action = ["PASS"]
    inv = _get_inv(obs, 0)
    pick = pick_task(tasks, farmer_pos, inv, obs)
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

    return {
        "farmer": farmer_action,
        "hands": [],
        "market": market_orders,
    }