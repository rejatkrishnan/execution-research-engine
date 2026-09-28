"""Deterministic replay of timestamped order-book events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .order_book import Fill, LimitOrderBook, MarketOrder, Order


@dataclass(frozen=True, slots=True)
class BookEvent:
    """A timestamped action applied to a limit order book."""

    timestamp: float
    action: str
    order: Order | MarketOrder | None = None
    order_id: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp < 0:
            raise ValueError("timestamp must be non-negative")
        if self.action not in {"add", "market", "cancel"}:
            raise ValueError(f"unsupported action: {self.action}")
        if self.action in {"add", "market"} and self.order is None:
            raise ValueError(f"{self.action} event requires order")
        if self.action == "cancel" and not self.order_id:
            raise ValueError("cancel event requires order_id")


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Result of applying one replay event."""

    event: BookEvent
    fills: tuple[Fill, ...]


def replay(
    events: Iterable[BookEvent],
    book: LimitOrderBook | None = None,
) -> tuple[ReplayResult, ...]:
    """Replay events in timestamp order against a limit order book.

    Events must already be sorted by non-decreasing timestamp. Rejecting
    out-of-order input keeps replay deterministic and makes bad datasets fail
    fast instead of being silently reordered.
    """
    target = book if book is not None else LimitOrderBook()
    results: list[ReplayResult] = []
    previous_timestamp: float | None = None

    for event in events:
        if previous_timestamp is not None and event.timestamp < previous_timestamp:
            raise ValueError("events must be sorted by timestamp")
        previous_timestamp = event.timestamp

        if event.action == "add":
            assert isinstance(event.order, Order)
            fills = target.add(event.order)
        elif event.action == "market":
            assert isinstance(event.order, MarketOrder)
            fills = target.execute_market(event.order)
        else:
            assert event.order_id is not None
            target.cancel(event.order_id)
            fills = ()

        results.append(ReplayResult(event=event, fills=fills))

    return tuple(results)
