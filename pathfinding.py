"""Pathfinding Engine for Kaggriculture Agent using Dijkstra Algorithm.

Provides robust 2D grid pathfinding, movement step generation, and obstacle mapping.
"""

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

# Directions mapping delta (dx, dy) to action strings
DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

DELTA_TO_DIR: Dict[Tuple[int, int], str] = {v: k for k, v in DIRECTIONS.items()}


def in_bounds(x: int, y: int, width: int = 10, height: int = 10) -> bool:
    """Check if coordinates (x, y) are within grid bounds."""
    return 0 <= x < width and 0 <= y < height


def dijkstra(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    width: int = 10,
    height: int = 10,
    blocked: Optional[Set[Tuple[int, int]]] = None,
    weights: Optional[Dict[Tuple[int, int], int]] = None,
) -> Tuple[List[Tuple[int, int]], float]:
    """Find the shortest path from start to goal on a 2D grid using Dijkstra's algorithm."""
    if blocked is None:
        blocked = set()
    if weights is None:
        weights = {}

    if not in_bounds(*start, width, height) or not in_bounds(*goal, width, height):
        return [], float("inf")
    if start in blocked or goal in blocked:
        return [], float("inf")
    if start == goal:
        return [start], 0.0

    pq: List[Tuple[float, Tuple[int, int]]] = [(0.0, start)]
    dist: Dict[Tuple[int, int], float] = {start: 0.0}
    prev: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}

    while pq:
        d, cur = heapq.heappop(pq)
        if cur == goal:
            break
        if d > dist.get(cur, float("inf")):
            continue

        cx, cy = cur
        for dx, dy in DIRECTIONS.values():
            nx, ny = cx + dx, cy + dy
            if not in_bounds(nx, ny, width, height) or (nx, ny) in blocked:
                continue
            step_cost = weights.get((nx, ny), 1)
            nd = d + step_cost
            if nd < dist.get((nx, ny), float("inf")):
                dist[(nx, ny)] = nd
                prev[(nx, ny)] = cur
                heapq.heappush(pq, (nd, (nx, ny)))

    if goal not in dist:
        return [], float("inf")

    path: List[Tuple[int, int]] = []
    node: Optional[Tuple[int, int]] = goal
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path, dist[goal]


def path_to_actions(path: List[Tuple[int, int]]) -> List[str]:
    """Convert a path of (x, y) coordinates into movement action strings."""
    actions: List[str] = []
    for i in range(1, len(path)):
        x0, y0 = path[i - 1]
        x1, y1 = path[i]
        delta = (x1 - x0, y1 - y0)
        if delta in DELTA_TO_DIR:
            actions.append(DELTA_TO_DIR[delta])
    return actions


def get_next_step(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    width: int = 10,
    height: int = 10,
    blocked: Optional[Set[Tuple[int, int]]] = None,
) -> str:
    """Calculate the immediate next movement action required to move from start to goal."""
    if start == goal:
        return "PASS"
    path, cost = dijkstra(start, goal, width=width, height=height, blocked=blocked)
    actions = path_to_actions(path)
    return actions[0] if actions else "PASS"


def extract_blocked_from_tiles(
    tiles: List[List[Any]],
    allow_locked_pass: bool = True
) -> Set[Tuple[int, int]]:
    """Extract blocked coordinates from the Kaggriculture tiles observation.
    
    Note: Locked tiles are passable for movement according to rules.
    """
    blocked: Set[Tuple[int, int]] = set()
    height = len(tiles)
    if height == 0:
        return blocked
    width = len(tiles[0])

    for y in range(height):
        for x in range(width):
            tile = tiles[y][x]
            if not allow_locked_pass and tile == "LOCKED":
                blocked.add((x, y))
            elif isinstance(tile, dict):
                if tile.get("kind") == "WEED":
                    blocked.add((x, y))
                elif tile.get("kind") in ("COOP", "PASTURE") and tile.get("animal"):
                    blocked.add((x, y))
    return blocked