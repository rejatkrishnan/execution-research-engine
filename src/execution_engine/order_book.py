"""Core limit-order-book primitives with price-time-priority matching."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class Order:
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


@dataclass(frozen=True, slots=True)
class Fill:
    taker_order_id: str
    maker_order_id: str
    price: float
    quantity: float


class LimitOrderBook:
    def __init__(self) -> None:
        self._bids: dict[float, OrderedDict[str, Order]] = {}
        self._asks: dict[float, OrderedDict[str, Order]] = {}
        self._orders: dict[str, Order] = {}

    def add(self, order: Order) -> tuple[Fill, ...]:
        """Submit a limit order, matching first and resting any remainder."""
        if order.order_id in self._orders:
            raise ValueError(f"duplicate order_id: {order.order_id}")

        remaining = order.quantity
        fills: list[Fill] = []
        opposite = self._asks if order.side is Side.BUY else self._bids

        while remaining > 0 and self._crosses(order.side, order.price):
            best_price = self.best_ask if order.side is Side.BUY else self.best_bid
            assert best_price is not None
            queue = opposite[best_price]

            while remaining > 0 and queue:
                maker_id, maker = next(iter(queue.items()))
                traded = min(remaining, maker.quantity)
                fills.append(Fill(order.order_id, maker_id, maker.price, traded))
                remaining -= traded

                if traded == maker.quantity:
                    del queue[maker_id]
                    del self._orders[maker_id]
                else:
                    updated = replace(maker, quantity=maker.quantity - traded)
                    queue[maker_id] = updated
                    self._orders[maker_id] = updated

            if not queue:
                del opposite[best_price]

        if remaining > 0:
            resting = replace(order, quantity=remaining)
            levels = self._bids if resting.side is Side.BUY else self._asks
            queue = levels.setdefault(resting.price, OrderedDict())
            queue[resting.order_id] = resting
            self._orders[resting.order_id] = resting

        return tuple(fills)

    def _crosses(self, side: Side, limit_price: float) -> bool:
        if side is Side.BUY:
            return self.best_ask is not None and limit_price >= self.best_ask
        return self.best_bid is not None and limit_price <= self.best_bid

    def cancel(self, order_id: str) -> Order:
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
        return max(self._bids, default=None)

    @property
    def best_ask(self) -> float | None:
        return min(self._asks, default=None)

    @property
    def spread(self) -> float | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid

    def level_quantity(self, side: Side, price: float) -> float:
        levels = self._bids if side is Side.BUY else self._asks
        return sum(order.quantity for order in levels.get(price, {}).values())

    def orders_at(self, side: Side, price: float) -> tuple[Order, ...]:
        levels = self._bids if side is Side.BUY else self._asks
        return tuple(levels.get(price, {}).values())

    def __len__(self) -> int:
        return len(self._orders)
