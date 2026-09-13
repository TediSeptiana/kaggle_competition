"""Market decision module for Kaggriculture.

Semua logika beli/jual di sini. Tidak peduli harga tinggi/rendah,
eksekusi saja sesuai CONFIG.
"""

from typing import Any, Dict, List


def decide_market_orders(obs: Dict[str, Any], config: Dict[str, Any]) -> List[List[Any]]:
    step = obs.get("step")
    if step is None:
        step = obs["day"] * 24 + obs["hour"]
    day = step // config["TURNS_PER_DAY"]

    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    if not farms or player >= len(farms):
        return []
    me = farms[player]
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {}) or {}
    seeds = private.get("seeds", {}) or {}

    orders: List[List[Any]] = []

    # -------------------------------------------------------------
    # HARI 0: setup belanja lengkap
    # -------------------------------------------------------------
    if step == 0:
        if config["BUY_GOOSE"]:
            orders.append(["BUY_ANIMAL", "GOOSE", config["BUY_GOOSE"]])
        if config["BUY_WHEAT_SEED"]:
            orders.append(["BUY_SEED", "WHEAT", config["BUY_WHEAT_SEED"]])
        if config["BUY_FERTILIZER"]:
            orders.append(["BUY_PRODUCT", "FERTILIZER", config["BUY_FERTILIZER"]])
        if config["BUY_WHEAT_FEED"]:
            orders.append(["BUY_PRODUCT", "WHEAT", config["BUY_WHEAT_FEED"]])
        if config["HIRE_HAND"]:
            orders.append(["HIRE"])
        return orders

    # -------------------------------------------------------------
    # MAINTENANCE HARIAN
    # -------------------------------------------------------------
    # Hire hand baru setiap hari
    if config["HIRE_HAND"]:
        orders.append(["HIRE"])

    # Beli pakan wheat
    if config["DAILY_BUY_WHEAT_FEED"] > 0:
        orders.append(["BUY_PRODUCT", "WHEAT", config["DAILY_BUY_WHEAT_FEED"]])

    # -------------------------------------------------------------
    # CYCLE WHEAT: beli seed tiap N hari
    # -------------------------------------------------------------
    cycle = config["WHEAT_CYCLE_DAYS"]
    if cycle > 0 and day > 0 and day % cycle == 0:
        have = seeds.get("WHEAT", 0)
        need = config["BUY_WHEAT_SEED"] - have
        if need > 0:
            orders.append(["BUY_SEED", "WHEAT", need])

    # -------------------------------------------------------------
    # JUAL HASIL
    # -------------------------------------------------------------
    if shed.get("EGG", 0) > 0:
        orders.append(["SELL", "EGG", shed["EGG"]])

    keep = config.get("KEEP_FERTILIZER", 0)
    if shed.get("FERTILIZER", 0) > keep:
        orders.append(["SELL", "FERTILIZER", shed["FERTILIZER"] - keep])

    # jual sisa wheat di shed (buffer di atas kebutuhan pakan harian)
    wheat_buffer = config.get("WHEAT_SHED_BUFFER", 10)
    if shed.get("WHEAT", 0) > wheat_buffer:
        orders.append(["SELL", "WHEAT", shed["WHEAT"] - wheat_buffer])

    return orders