"""Pathfinding + locator module for Kaggriculture.

Berisi:
  - Dijkstra untuk navigasi
  - Dijkstra All untuk menghitung jarak ke semua tile
  - Locator: fungsi cari tile untuk build / plant / harvest / dll

Semua koordinat dalam GAME COORDS
(0..9 untuk boardSize=10).

Format koordinat:
    (x, y)

Arah:
    NORTH = y - 1
    SOUTH = y + 1
    EAST  = x + 1
    WEST  = x - 1
"""

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple


# =====================================================================
# TYPE
# =====================================================================

Coord = Tuple[int, int]


# =====================================================================
# DIRECTION
# =====================================================================

DIRECTIONS: Dict[str, Coord] = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

DELTA_TO_DIR = {
    delta: direction
    for direction, delta in DIRECTIONS.items()
}


# =====================================================================
# DIJKSTRA
# =====================================================================

def dijkstra(
    start: Coord,
    goal: Coord,
    width: int = 10,
    height: int = 10,
    blocked: Optional[Set[Coord]] = None,
    weights: Optional[Dict[Coord, float]] = None,
) -> Tuple[List[Coord], float]:
    """Cari shortest path dari start ke goal menggunakan Dijkstra.

    Args:
        start:
            Posisi awal player.

        goal:
            Posisi tujuan.

        width:
            Lebar board.

        height:
            Tinggi board.

        blocked:
            Set tile yang tidak bisa dilewati.

        weights:
            Movement cost setiap tile.
            Contoh:
                {
                    (2, 3): 2,
                    (3, 3): 5,
                }

    Returns:
        (path, distance)

        Jika tidak ada jalan:
            ([], inf)
    """

    blocked = blocked or set()
    weights = weights or {}

    # Validasi start
    if not (
        0 <= start[0] < width
        and 0 <= start[1] < height
    ):
        return [], float("inf")

    # Validasi goal
    if not (
        0 <= goal[0] < width
        and 0 <= goal[1] < height
    ):
        return [], float("inf")

    # Start / goal tidak boleh blocked
    if start in blocked or goal in blocked:
        return [], float("inf")

    # Start == goal
    if start == goal:
        return [start], 0.0

    # Priority queue
    pq: List[Tuple[float, Coord]] = [
        (0.0, start)
    ]

    # Jarak terpendek
    dist: Dict[Coord, float] = {
        start: 0.0
    }

    # Parent untuk reconstruct path
    prev: Dict[Coord, Optional[Coord]] = {
        start: None
    }

    while pq:
        current_distance, current = heapq.heappop(pq)

        # Abaikan entry lama
        if current_distance > dist.get(
            current,
            float("inf")
        ):
            continue

        # Goal sudah ditemukan
        if current == goal:
            break

        cx, cy = current

        # Cek 4 arah
        for dx, dy in DIRECTIONS.values():
            nx = cx + dx
            ny = cy + dy

            next_tile = (nx, ny)

            # Di luar board
            if not (
                0 <= nx < width
                and 0 <= ny < height
            ):
                continue

            # Tile blocked
            if next_tile in blocked:
                continue

            # Movement cost
            cost = weights.get(next_tile, 1)

            # Hindari weight negatif / nol
            if cost <= 0:
                cost = 1

            new_distance = current_distance + cost

            # Jalur lebih murah
            if new_distance < dist.get(
                next_tile,
                float("inf")
            ):
                dist[next_tile] = new_distance
                prev[next_tile] = current

                heapq.heappush(
                    pq,
                    (new_distance, next_tile)
                )

    # Goal tidak reachable
    if goal not in dist:
        return [], float("inf")

    # --------------------------------------------------------------
    # RECONSTRUCT PATH
    # --------------------------------------------------------------

    path: List[Coord] = []

    node: Optional[Coord] = goal

    while node is not None:
        path.append(node)
        node = prev[node]

    path.reverse()

    return path, dist[goal]


# =====================================================================
# DIJKSTRA ALL
# =====================================================================

def dijkstra_all(
    start: Coord,
    width: int = 10,
    height: int = 10,
    blocked: Optional[Set[Coord]] = None,
    weights: Optional[Dict[Coord, float]] = None,
) -> Dict[Coord, float]:
    """Hitung jarak dari start ke SEMUA tile yang reachable.

    Ini lebih efisien untuk Locator karena kita tidak perlu
    menjalankan Dijkstra berkali-kali untuk setiap kandidat tile.

    Returns:
        {
            (x, y): distance,
            ...
        }

    Tile yang tidak reachable tidak akan ada di dictionary.
    """

    blocked = blocked or set()
    weights = weights or {}

    # Validasi start
    if not (
        0 <= start[0] < width
        and 0 <= start[1] < height
    ):
        return {}

    # Start blocked
    if start in blocked:
        return {}

    # Priority queue
    pq: List[Tuple[float, Coord]] = [
        (0.0, start)
    ]

    # Distance map
    dist: Dict[Coord, float] = {
        start: 0.0
    }

    while pq:
        current_distance, current = heapq.heappop(pq)

        # Abaikan entry lama
        if current_distance > dist.get(
            current,
            float("inf")
        ):
            continue

        cx, cy = current

        # Cek 4 arah
        for dx, dy in DIRECTIONS.values():
            nx = cx + dx
            ny = cy + dy

            next_tile = (nx, ny)

            # Di luar board
            if not (
                0 <= nx < width
                and 0 <= ny < height
            ):
                continue

            # Blocked
            if next_tile in blocked:
                continue

            # Movement cost
            cost = weights.get(next_tile, 1)

            if cost <= 0:
                cost = 1

            new_distance = current_distance + cost

            # Ditemukan jalur yang lebih murah
            if new_distance < dist.get(
                next_tile,
                float("inf")
            ):
                dist[next_tile] = new_distance

                heapq.heappush(
                    pq,
                    (new_distance, next_tile)
                )

    return dist


# =====================================================================
# PATH -> ACTION
# =====================================================================

def path_to_actions(
    path: List[Coord],
) -> List[str]:
    """Konversi path menjadi action direction."""

    actions: List[str] = []

    for i in range(1, len(path)):
        previous = path[i - 1]
        current = path[i]

        delta = (
            current[0] - previous[0],
            current[1] - previous[1],
        )

        direction = DELTA_TO_DIR.get(delta)

        if direction is not None:
            actions.append(direction)

    return actions


# =====================================================================
# GET ROUTE
# =====================================================================

def get_route_actions(
    start: Coord,
    goal: Coord,
    width: int = 10,
    height: int = 10,
    blocked: Optional[Set[Coord]] = None,
    weights: Optional[Dict[Coord, float]] = None,
) -> List[str]:
    """Cari route dari start ke goal dan return actions."""

    path, _ = dijkstra(
        start=start,
        goal=goal,
        width=width,
        height=height,
        blocked=blocked,
        weights=weights,
    )

    return path_to_actions(path)


# =====================================================================
# OBSTACLE
# =====================================================================

def extract_blocked_from_tiles(tiles):
    """Di Kaggriculture, tidak ada tile yang benar-benar memblok navigasi.

    - LOCKED             : passable (hanya action tile-nya no-op)
    - WEED               : passable (hanya tidak bisa ditanami)
    - COOP/PASTURE animal: passable (farmer HARUS bisa berdiri di atasnya
                           untuk FEED / HARVEST / COLLECT_FERTILIZER / CARE)
    """
    return set()


# =====================================================================
# MANHATTAN
# =====================================================================

def manhattan(
    a: Coord,
    b: Coord,
) -> int:
    """Manhattan distance.

    Ini hanya jarak geometris.
    Tidak memperhitungkan obstacle.
    """

    return (
        abs(a[0] - b[0])
        + abs(a[1] - b[1])
    )


# =====================================================================
# SORT BY MANHATTAN
# =====================================================================

def sort_by_distance(
    tiles: List[Coord],
    origin: Coord,
) -> List[Coord]:
    """Sort tile berdasarkan Manhattan distance."""

    return sorted(
        tiles,
        key=lambda tile: manhattan(tile, origin)
    )


# =====================================================================
# ITERATE TILES
# =====================================================================

def _iter_tiles(
    tiles: List[List[Any]],
):
    """Iterate semua tile.

    Yield:
        x, y, tile
    """

    height = len(tiles)

    width = (
        len(tiles[0])
        if height
        else 0
    )

    for y in range(height):
        for x in range(width):
            yield x, y, tiles[y][x]


# =====================================================================
# EMPTY TILES
# =====================================================================

def find_empty_tiles(
    tiles: List[List[Any]],
    row: Optional[int] = None,
) -> List[Coord]:
    """Cari tile kosong (None).

    Jika row diberikan, hanya mencari pada row tersebut.
    """

    out: List[Coord] = []

    for x, y, tile in _iter_tiles(tiles):

        if row is not None and y != row:
            continue

        if tile is None:
            out.append((x, y))

    return out


# =====================================================================
# BUILD COOP
# =====================================================================

def find_build_tiles(
    tiles: List[List[Any]],
    target_count: int,
    row: int,
    origin: Coord,
) -> List[Coord]:
    """Cari tile untuk BUILD_COOP.

    Prinsip:
        1. Tile harus kosong.
        2. Tile harus reachable.
        3. Pilih tile TERJAUH dari player.

    Return:
        Maksimal target_count tile.
    """

    if target_count <= 0:
        return []

    height = len(tiles)

    width = (
        len(tiles[0])
        if height
        else 0
    )

    # Ambil obstacle
    blocked = extract_blocked_from_tiles(tiles)

    # Hitung jarak dari origin ke semua tile
    distances = dijkstra_all(
        start=origin,
        width=width,
        height=height,
        blocked=blocked,
    )

    candidates: List[Tuple[Coord, float]] = []

    # Kandidat tile kosong
    empty_tiles = find_empty_tiles(
        tiles,
        row=row,
    )

    for tile in empty_tiles:

        # Tile tidak reachable
        if tile not in distances:
            continue

        distance = distances[tile]

        candidates.append(
            (tile, distance)
        )

    # TERJAUH dulu
    candidates.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        tile
        for tile, _ in candidates[:target_count]
    ]


# =====================================================================
# PLANT
# =====================================================================

def find_plant_tiles(
    tiles: List[List[Any]],
    target_count: int,
    row: int,
    origin: Coord,
    crop: str = "WHEAT",
) -> List[Coord]:
    """Cari tile untuk PLANT.

    Prinsip:
        1. Hitung jumlah crop yang sudah ada.
        2. Kalau target sudah tercapai -> [].
        3. Cari tile kosong.
        4. Tile harus reachable.
        5. Pilih tile TERDEKAT.

    Return:
        Maksimal tile yang dibutuhkan.
    """

    if target_count <= 0:
        return []

    # --------------------------------------------------------------
    # HITUNG CROP YANG SUDAH ADA
    # --------------------------------------------------------------

    current = sum(
        1
        for _, _, tile in _iter_tiles(tiles)
        if (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile.get("crop") == crop
        )
    )

    # Berapa tambahan yang dibutuhkan?
    need = target_count - current

    if need <= 0:
        return []

    # --------------------------------------------------------------
    # BOARD SIZE
    # --------------------------------------------------------------

    height = len(tiles)

    width = (
        len(tiles[0])
        if height
        else 0
    )

    # --------------------------------------------------------------
    # OBSTACLE
    # --------------------------------------------------------------

    blocked = extract_blocked_from_tiles(tiles)

    # --------------------------------------------------------------
    # DIJKSTRA
    # --------------------------------------------------------------

    distances = dijkstra_all(
        start=origin,
        width=width,
        height=height,
        blocked=blocked,
    )

    # --------------------------------------------------------------
    # CANDIDATE
    # --------------------------------------------------------------

    candidates: List[Tuple[Coord, float]] = []

    empty_tiles = find_empty_tiles(
        tiles,
        row=row,
    )

    for tile in empty_tiles:

        # Tidak reachable
        if tile not in distances:
            continue

        distance = distances[tile]

        candidates.append(
            (tile, distance)
        )

    # TERDEKAT dulu
    candidates.sort(
        key=lambda item: item[1]
    )

    return [
        tile
        for tile, _ in candidates[:need]
    ]


# =====================================================================
# HARVEST
# =====================================================================
CROP_FIRST_YIELD_DAY = {
    "WHEAT": 2, "CARROT": 2, "TOMATO": 8,
    "STRAWBERRY": 10, "MELON": 10,
}
ANIMAL_FIRST_YIELD_DAY = {
    "GOOSE": 4, "COW": 8, "SHEEP": 6,
}


def find_harvest_tiles(tiles, current_day):
    """Tile yang BENAR-BENAR siap dipanen (age >= first_yield_day)."""
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
            if age >= CROP_FIRST_YIELD_DAY.get(crop, 2):
                out.append((x, y))

        elif kind in ("COOP", "PASTURE"):
            animal = tile.get("animal")
            if not animal:
                continue
            age = current_day - tile.get("placed_day", current_day)
            if age >= ANIMAL_FIRST_YIELD_DAY.get(animal, 4):
                out.append((x, y))

    return out


# =====================================================================
# PLACE GOOSE
# =====================================================================

def find_place_goose_tiles(
    tiles: List[List[Any]],
) -> List[Coord]:
    """Cari Coop yang kosong dan belum memiliki goose."""

    out: List[Coord] = []

    for x, y, tile in _iter_tiles(tiles):

        if (
            isinstance(tile, dict)
            and tile.get("kind") == "COOP"
            and tile.get("animal") is None
        ):
            out.append((x, y))

    return out


# =====================================================================
# COLLECT FERTILIZER
# =====================================================================

def find_collect_fertilizer_tiles(
    tiles: List[List[Any]],
) -> List[Coord]:
    """Cari animal yang fertilizer_available == True."""

    out: List[Coord] = []

    for x, y, tile in _iter_tiles(tiles):

        if (
            isinstance(tile, dict)
            and tile.get("kind") in ("COOP", "PASTURE")
            and tile.get("fertilizer_available")
        ):
            out.append((x, y))

    return out


# =====================================================================
# FEED
# =====================================================================

def find_feed_tiles(
    tiles: List[List[Any]],
) -> List[Coord]:
    """Cari animal yang belum di-feed hari ini."""

    out: List[Coord] = []

    for x, y, tile in _iter_tiles(tiles):

        if (
            isinstance(tile, dict)
            and tile.get("kind") in ("COOP", "PASTURE")
            and tile.get("animal")
            and not tile.get("fed_today")
        ):
            out.append((x, y))

    return out


# =====================================================================
# WATER
# =====================================================================

def find_water_tiles(
    tiles: List[List[Any]],
) -> List[Coord]:
    """Cari plant yang belum di-water hari ini."""

    out: List[Coord] = []

    for x, y, tile in _iter_tiles(tiles):

        if (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and not tile.get("watered_today")
        ):
            out.append((x, y))

    return out


# =====================================================================
# FERTILIZE
# =====================================================================

def find_fertilize_tiles(
    tiles: List[List[Any]],
) -> List[Coord]:
    """Cari plant yang belum di-fertilize."""

    out: List[Coord] = []

    for x, y, tile in _iter_tiles(tiles):

        if (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile.get(
                "fertilized_until_day",
                -1,
            ) < 0
        ):
            out.append((x, y))

    return out