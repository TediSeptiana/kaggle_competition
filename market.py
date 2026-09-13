"""Market decision module for Kaggriculture.

Semua logika beli/jual di sini. Tidak peduli harga tinggi/rendah,
eksekusi saja sesuai CONFIG.
"""

from typing import Any, Dict, List


def decide_market_orders(obs, config):
    step = obs.get("step") or obs["day"]*24 + obs["hour"]
    day = step // config["TURNS_PER_DAY"]

    player = obs.get("player", 0)
    me = obs["farms"][player]
    priv = obs.get("private", {}) or {}
    shed = priv.get("shed", {}) or {}
    seeds = priv.get("seeds", {}) or {}

    orders = []

    # Step 0: belanja setup
    if step == 0:
        orders.append(["BUY_ANIMAL", "GOOSE", config["BUY_GOOSE"]])
        orders.append(["BUY_SEED", "WHEAT", config["BUY_WHEAT_SEED"]])
        orders.append(["BUY_PRODUCT", "FERTILIZER", config["BUY_FERTILIZER"]])
        orders.append(["BUY_PRODUCT", "WHEAT", config["BUY_WHEAT_FEED"]])
        return orders

    # Wheat cycle: beli seed baru tiap N hari
    cycle = config["WHEAT_CYCLE_DAYS"]
    if cycle > 0 and day > 0 and day % cycle == 0:
        have = seeds.get("WHEAT", 0)
        need = config["BUY_WHEAT_SEED"] - have
        if need > 0:
            orders.append(["BUY_SEED", "WHEAT", need])

    # Beli pakan wheat tiap hari
    if config["DAILY_BUY_WHEAT_FEED"] > 0:
        orders.append(["BUY_PRODUCT", "WHEAT", config["DAILY_BUY_WHEAT_FEED"]])

    # Jual hasil
    if shed.get("EGG", 0) > 0:
        orders.append(["SELL", "EGG", shed["EGG"]])
    if shed.get("FERTILIZER", 0) > config["KEEP_FERTILIZER"]:
        orders.append(["SELL", "FERTILIZER",
                       shed["FERTILIZER"] - config["KEEP_FERTILIZER"]])
    if shed.get("WHEAT", 0) > config["WHEAT_SHED_BUFFER"]:
        orders.append(["SELL", "WHEAT",
                       shed["WHEAT"] - config["WHEAT_SHED_BUFFER"]])

    return orders