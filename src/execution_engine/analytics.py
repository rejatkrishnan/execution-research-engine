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


@dataclass(frozen=True, slots=True)
class ImplementationShortfall:
    """Implementation shortfall decomposition for a parent order."""

    target_quantity: float
    filled_quantity: float
    unfilled_quantity: float
    fill_rate: float
    execution_cost: float
    opportunity_cost: float
    total_cost: float
    total_cost_bps: float


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


def implementation_shortfall(
    fills: Iterable[Fill],
    side: Side,
    arrival_price: float,
    target_quantity: float,
    final_price: float | None = None,
) -> ImplementationShortfall:
    """Decompose implementation shortfall into execution and opportunity cost.

    Costs are signed from the parent order's perspective: positive values are
    adverse and negative values are favorable. For partially filled orders,
    final_price is required to value the unfilled remainder.
    """
    if arrival_price <= 0:
        raise ValueError("arrival_price must be positive")
    if target_quantity <= 0:
        raise ValueError("target_quantity must be positive")
    if final_price is not None and final_price <= 0:
        raise ValueError("final_price must be positive")

    fill_list = tuple(fills)
    if any(fill.quantity <= 0 for fill in fill_list):
        raise ValueError("fill quantities must be positive")

    filled_quantity = sum(fill.quantity for fill in fill_list)
    tolerance = 1e-12 * max(1.0, target_quantity)
    if filled_quantity - target_quantity > tolerance:
        raise ValueError("filled quantity cannot exceed target_quantity")

    unfilled_quantity = max(0.0, target_quantity - filled_quantity)
    if unfilled_quantity > tolerance and final_price is None:
        raise ValueError("final_price is required for a partially filled order")

    direction = 1.0 if side is Side.BUY else -1.0
    execution_notional = sum(fill.price * fill.quantity for fill in fill_list)
    execution_cost = direction * (
        execution_notional - arrival_price * filled_quantity
    )

    opportunity_cost = 0.0
    if unfilled_quantity > tolerance:
        assert final_price is not None
        opportunity_cost = (
            direction * (final_price - arrival_price) * unfilled_quantity
        )

    total_cost = execution_cost + opportunity_cost
    benchmark_notional = arrival_price * target_quantity
    total_cost_bps = total_cost / benchmark_notional * 10_000.0

    return ImplementationShortfall(
        target_quantity=target_quantity,
        filled_quantity=filled_quantity,
        unfilled_quantity=unfilled_quantity,
        fill_rate=filled_quantity / target_quantity,
        execution_cost=execution_cost,
        opportunity_cost=opportunity_cost,
        total_cost=total_cost,
        total_cost_bps=total_cost_bps,
    )
