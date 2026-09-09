"""Core limit-order-book primitives.

The first implementation intentionally focuses on resting liquidity. Matching and
trade generation will be layered on top of this book in later iterations.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum


class Side(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class Order:
    """A resting limit order."""

    order_id: str
    side: Side
    price: float
    quantity: float

    def __post_init__(self) -> None:
        if not self.order_id:
            raise ValueError("order_id must be non-empty")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


class LimitOrderBook:
    """In-memory limit order book with FIFO queues at each price level."""

    def __init__(self) -> None:
        self._bids: dict[float, OrderedDict[str, Order]] = {}
        self._asks: dict[float, OrderedDict[str, Order]] = {}
        self._orders: dict[str, Order] = {}

    def add(self, order: Order) -> None:
        """Add a resting order while preserving price-level insertion order."""
        if order.order_id in self._orders:
            raise ValueError(f"duplicate order_id: {order.order_id}")

        levels = self._bids if order.side is Side.BUY else self._asks
        queue = levels.setdefault(order.price, OrderedDict())
        queue[order.order_id] = order
        self._orders[order.order_id] = order

    def cancel(self, order_id: str) -> Order:
        """Cancel an order and return the removed order."""
        try:
            order = self._orders.pop(order_id)
        except KeyError as exc:
            raise KeyError(f"unknown order_id: {order_id}") from exc

        levels = self._bids if order.side is Side.BUY else self._asks
        queue = levels[order.price]
        del queue[order_id]
        if not queue:
            del levels[order.price]
        return order

    @property
    def best_bid(self) -> float | None:
        """Highest resting bid price."""
        return max(self._bids, default=None)

    @property
    def best_ask(self) -> float | None:
        """Lowest resting ask price."""
        return min(self._asks, default=None)

    @property
    def spread(self) -> float | None:
        """Top-of-book spread, or None when either side is empty."""
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid

    def level_quantity(self, side: Side, price: float) -> float:
        """Total resting quantity at a price level."""
        levels = self._bids if side is Side.BUY else self._asks
        return sum(order.quantity for order in levels.get(price, {}).values())

    def orders_at(self, side: Side, price: float) -> tuple[Order, ...]:
        """Orders at a price level in FIFO priority order."""
        levels = self._bids if side is Side.BUY else self._asks
        return tuple(levels.get(price, {}).values())

    def __len__(self) -> int:
        return len(self._orders)
