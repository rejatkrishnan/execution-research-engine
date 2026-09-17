"""Execution-quality metrics derived from fill records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .order_book import Fill, Side


@dataclass(frozen=True, slots=True)
class ExecutionSummary:
    """Aggregate execution statistics for a set of fills."""

    quantity: float
    notional: float
    vwap: float


def summarize_fills(fills: Iterable[Fill]) -> ExecutionSummary:
    """Return filled quantity, notional, and volume-weighted average price."""
    fill_list = tuple(fills)
    quantity = sum(fill.quantity for fill in fill_list)
    if quantity <= 0:
        raise ValueError("at least one positive-quantity fill is required")

    notional = sum(fill.price * fill.quantity for fill in fill_list)
    return ExecutionSummary(quantity=quantity, notional=notional, vwap=notional / quantity)


def slippage_bps(fills: Iterable[Fill], side: Side, reference_price: float) -> float:
    """Return signed execution slippage versus a reference price in basis points.

    Positive values represent worse execution for the taker: paying above the
    reference for buys or selling below it for sells. Negative values represent
    price improvement.
    """
    if reference_price <= 0:
        raise ValueError("reference_price must be positive")

    vwap = summarize_fills(fills).vwap
    direction = 1.0 if side is Side.BUY else -1.0
    return direction * (vwap - reference_price) / reference_price * 10_000.0
