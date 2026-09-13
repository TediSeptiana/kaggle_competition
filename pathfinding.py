"""Pathfinding + locator module for Kaggriculture.

Berisi:
  - Dijkstra untuk navigasi
  - Dijkstra All untuk menghitung jarak ke semua tile
  - Locator: fungsi cari tile untuk build / plant / harvest / dll

Semua koordinat dalam GAME COORDS (0..9 untuk boardSize=10).
"""

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

Coord = Tuple[int, int]

DIRECTIONS: Dict[str, Coord] = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

DELTA_TO_DIR = {delta: d for d, delta in DIRECTIONS.items()}


# =====================================================================
# DIJKSTRA
# =====================================================================
def dijkstra(start, goal, width=10, height=10, blocked=None, weights=None):
    blocked = blocked or set()
    weights = weights or {}
    if not (0 <= start[0] < width and 0 <= start[1] < height):
        return [], float("inf")
    if not (0 <= goal[0] < width and 0 <= goal[1] < height):
        return [], float("inf")
    if start in blocked or goal in blocked:
        return [], float("inf")
    if start == goal:
        return [start], 0.0

    pq = [(0.0, start)]
    dist = {start: 0.0}
    prev = {start: None}
    while pq:
        d, cur = heapq.heappop(pq)
        if cur == goal:
            break
        if d > dist.get(cur, float("inf")):
            continue
        cx, cy = cur
        for dx, dy in DIRECTIONS.values():
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in blocked:
                continue
            nd = d + weights.get((nx, ny), 1)
            if nd < dist.get((nx, ny), float("inf")):
                dist[(nx, ny)] = nd
                prev[(nx, ny)] = cur
                heapq.heappush(pq, (nd, (nx, ny)))
    if goal not in dist:
        return [], float("inf")

    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path, dist[goal]


def dijkstra_all(start, width=10, height=10, blocked=None, weights=None):
    blocked = blocked or set()
    weights = weights or {}
    if not (0 <= start[0] < width and 0 <= start[1] < height):
        return {}
    if start in blocked:
        return {}

    pq = [(0.0, start)]
    dist = {start: 0.0}
    while pq:
        d, cur = heapq.heappop(pq)
        if d > dist.get(cur, float("inf")):
            continue
        cx, cy = cur
        for dx, dy in DIRECTIONS.values():
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in blocked:
                continue
            nd = d + weights.get((nx, ny), 1)
            if nd < dist.get((nx, ny), float("inf")):
                dist[(nx, ny)] = nd
                heapq.heappush(pq, (nd, (nx, ny)))
    return dist


# =====================================================================
# PATH → ACTIONS
# =====================================================================
def path_to_actions(path):
    actions = []
    for i in range(1, len(path)):
        delta = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        d = DELTA_TO_DIR.get(delta)
        if d is not None:
            actions.append(d)
    return actions


def get_route_actions(start, goal, width=10, height=10, blocked=None, weights=None):
    """Cari route dari start ke goal dan return actions."""
    path, _ = dijkstra(start, goal, width=width, height=height,
                       blocked=blocked, weights=weights)
    return path_to_actions(path)


# =====================================================================
# OBSTACLE
# =====================================================================
def extract_blocked_from_tiles(tiles):
    """Di Kaggriculture, tidak ada tile yang benar-benar memblok navigasi."""
    return set()


# =====================================================================
# UTILITAS JARAK
# =====================================================================
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def sort_by_distance(tiles, origin):
    return sorted(tiles, key=lambda t: manhattan(t, origin))


# =====================================================================
# ITERATE
# =====================================================================
def _iter_tiles(tiles):
    H = len(tiles)
    W = len(tiles[0]) if H else 0
    for y in range(H):
        for x in range(W):
            yield x, y, tiles[y][x]


def find_empty_tiles(tiles, row=None):
    out = []
    for x, y, tile in _iter_tiles(tiles):
        if row is not None and y != row:
            continue
        if tile is None:
            out.append((x, y))
    return out


# =====================================================================
# LOCATOR
# =====================================================================
def find_harvest_tiles(tiles, current_day):
    CROP_FIRST = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8,
                  "STRAWBERRY": 10, "MELON": 10}
    ANIMAL_FIRST = {"GOOSE": 4, "COW": 8, "SHEEP": 6}
    out = []
    for x, y, tile in _iter_tiles(tiles):
        if not isinstance(tile, dict):
            continue
        if tile.get("yield_units", 0) <= 0:
            continue
        kind = tile.get("kind")
        if kind == "PLANT":
            crop = tile.get("crop", "")
            age = current_day - tile.get("planted_day", current_day)
            if age >= CROP_FIRST.get(crop, 2):
                out.append((x, y))
        elif kind in ("COOP", "PASTURE"):
            animal = tile.get("animal")
            if not animal:
                continue
            age = current_day - tile.get("placed_day", current_day)
            if age >= ANIMAL_FIRST.get(animal, 4):
                out.append((x, y))
    return out


def find_place_goose_tiles(tiles):
    out = []
    for x, y, tile in _iter_tiles(tiles):
        if isinstance(tile, dict) and tile.get("kind") == "COOP" \
           and tile.get("animal") is None:
            out.append((x, y))
    return out


def find_collect_fertilizer_tiles(tiles):
    out = []
    for x, y, tile in _iter_tiles(tiles):
        if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") \
           and tile.get("fertilizer_available"):
            out.append((x, y))
    return out


def find_feed_tiles(tiles):
    out = []
    for x, y, tile in _iter_tiles(tiles):
        if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") \
           and tile.get("animal") and not tile.get("fed_today"):
            out.append((x, y))
    return out


def find_water_tiles(tiles):
    out = []
    for x, y, tile in _iter_tiles(tiles):
        if isinstance(tile, dict) and tile.get("kind") == "PLANT" \
           and not tile.get("watered_today"):
            out.append((x, y))
    return out


def find_fertilize_tiles(tiles):
    out = []
    for x, y, tile in _iter_tiles(tiles):
        if isinstance(tile, dict) and tile.get("kind") == "PLANT" \
           and tile.get("fertilized_until_day", -1) < 0:
            out.append((x, y))
    return out


# =====================================================================
# BUILD & PLANT (dengan list eksplisit opsional)
# =====================================================================
def find_build_tiles(tiles, target_count, row, origin):
    """Fallback: build di baris row, tile kosong terdekat."""
    empty = find_empty_tiles(tiles, row=row)
    if not empty:
        return []
    return sort_by_distance(empty, origin)[:target_count]


def find_plant_tiles(tiles, target_count, row, origin, crop="WHEAT"):
    current = sum(1 for _, _, t in _iter_tiles(tiles)
                  if isinstance(t, dict) and t.get("kind") == "PLANT"
                  and t.get("crop") == crop)
    need = target_count - current
    if need <= 0:
        return []
    empty = find_empty_tiles(tiles, row=row)
    return sort_by_distance(empty, origin)[:need]