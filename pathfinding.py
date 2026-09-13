"""Module for grid navigation and pathfinding algorithms in Kaggriculture."""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

# Vector offsets for orthogonal movement (NORTH, SOUTH, EAST, WEST)
DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

Position = Tuple[int, int]


def get_next_step(
    start: Position,
    target: Position,
    board_size: int = 10,
    blocked_tiles: Optional[Set[Position]] = None,
) -> Optional[str]:
    """Finds the immediate next direction move towards target using BFS (Shortest Path).

    Args:
        start: Current (x, y) position.
        target: Target (x, y) position.
        board_size: Grid width/height.
        blocked_tiles: Set of coordinates that cannot be traversed.

    Returns:
        Direction string ("NORTH", "SOUTH", "EAST", "WEST") or None if already at target or unreachable.
    """
    if start == target:
        return None

    blocked = blocked_tiles or set()
    queue: deque[Tuple[Position, List[str]]] = deque([(start, [])])
    visited: Set[Position] = {start}

    while queue:
        (curr_x, curr_y), path = queue.popleft()

        for direction, (dx, dy) in DIRECTIONS.items():
            nx, ny = curr_x + dx, curr_y + dy

            if 0 <= nx < board_size and 0 <= ny < board_size:
                next_pos = (nx, ny)

                if next_pos == target:
                    return path[0] if path else direction

                if next_pos not in visited and next_pos not in blocked:
                    visited.add(next_pos)
                    queue.append((next_pos, path + [direction]))

    return None


def get_closest_target(
    start: Position,
    candidates: List[Position],
    board_size: int = 10,
) -> Optional[Tuple[Position, str]]:
    """Finds the closest reachable candidate target and the first step direction towards it.

    Args:
        start: Current worker (x, y) position.
        candidates: List of potential target (x, y) positions.
        board_size: Grid dimensions.

    Returns:
        Tuple of (target_position, direction) or None.
    """
    if not candidates:
        return None

    best_target: Optional[Position] = None
    best_step: Optional[str] = None
    min_dist = float("inf")

    for cand in candidates:
        dist = abs(start[0] - cand[0]) + abs(start[1] - cand[1])
        if dist < min_dist:
            step = get_next_step(start, cand, board_size=board_size)
            if step or start == cand:
                min_dist = dist
                best_target = cand
                best_step = step

    if best_target and best_step:
        return best_target, best_step
    return None
"""
[cite: 1]
"""