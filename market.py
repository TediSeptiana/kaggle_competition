"""Market Intelligence Engine for Kaggriculture.

Handles smart selling to prevent price crashes and automated buying logic based on cash reserves.
"""

from typing import Any, Dict, List


class MarketManager:
    """Manages dynamic price evaluation and market order execution."""

    @staticmethod
    def get_market_orders(
        obs: Dict[str, Any],
        my_farm: Dict[str, Any],
        private: Dict[str, Any]
    ) -> List[List[Any]]:
        """Determine economic market orders for the current turn."""
        orders: List[List[Any]] = []
        step: int = obs.get("step", 0)
        hour: int = obs.get("hour", step % 24)
        money: float = my_farm.get("money", 0.0)

        shed: Dict[str, int] = private.get("shed", {}) or {}
        market_obs: Dict[str, Any] = obs.get("market", {}) or {}
        prices: Dict[str, float] = market_obs.get("prices", {})

        # Day 0 Setup Purchases
        if step == 0:
            orders.append(["BUY_ANIMAL", "GOOSE", 5])
            orders.append(["BUY_SEED", "WHEAT", 5])
            orders.append(["BUY_PRODUCT", "FERTILIZER", 5])
            orders.append(["HIRE"])
            return orders

        # Execute market decisions at start of each day (hour 0) or when shed is full
        shed_total = sum(shed.values())
        if hour == 0 or shed_total > 80:
            # 1. Sell high-margin goods with thresholding to prevent price crash
            sell_thresholds = {
                "EGG": 35,
                "WHEAT": 18,
                "FERTILIZER": 60,
                "MILK": 120,
                "WOOL": 150,
                "MELON": 180,
            }

            for item, qty in shed.items():
                if qty <= 0:
                    continue
                current_price = prices.get(item, 0)
                min_price = sell_thresholds.get(item, 10)

                if current_price >= min_price:
                    # Sell in small batches of max 5 units per turn to prevent glut
                    sell_amount = min(qty, 5)
                    orders.append(["SELL", item, sell_amount])

            # 2. Buy Wheat feed if stock is low
            if shed.get("WHEAT", 0) < 5 and money >= 100:
                orders.append(["BUY_PRODUCT", "WHEAT", 5])

            # 3. Daily Farm Hand Hiring Strategy
            if money >= 200 and my_farm.get("hires_today", 0) == 0:
                orders.append(["HIRE"])

        return orders[:10]  # Respect maxMarketOrdersPerTurn limit