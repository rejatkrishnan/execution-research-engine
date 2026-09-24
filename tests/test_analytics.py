import pytest

from execution_engine import (
    Fill,
    Side,
    implementation_shortfall,
    slippage_bps,
    summarize_fills,
)


def test_summarize_fills_calculates_quantity_notional_and_vwap() -> None:
    fills = (
        Fill("m1", "a1", 100.0, 1.0),
        Fill("m1", "a2", 102.0, 3.0),
    )

    summary = summarize_fills(fills)

    assert summary.quantity == 4.0
    assert summary.notional == 406.0
    assert summary.vwap == 101.5


def test_buy_slippage_is_positive_when_execution_is_above_reference() -> None:
    fills = (Fill("m1", "a1", 101.0, 2.0),)
    assert slippage_bps(fills, Side.BUY, 100.0) == pytest.approx(100.0)


def test_sell_slippage_is_positive_when_execution_is_below_reference() -> None:
    fills = (Fill("m1", "b1", 99.0, 2.0),)
    assert slippage_bps(fills, Side.SELL, 100.0) == pytest.approx(100.0)


def test_price_improvement_produces_negative_slippage() -> None:
    fills = (Fill("m1", "a1", 99.5, 1.0),)
    assert slippage_bps(fills, Side.BUY, 100.0) == pytest.approx(-50.0)


def test_implementation_shortfall_for_fully_filled_buy() -> None:
    fills = (
        Fill("m1", "a1", 100.0, 1.0),
        Fill("m1", "a2", 102.0, 3.0),
    )

    result = implementation_shortfall(
        fills,
        Side.BUY,
        arrival_price=100.0,
        target_quantity=4.0,
    )

    assert result.filled_quantity == 4.0
    assert result.unfilled_quantity == 0.0
    assert result.fill_rate == 1.0
    assert result.execution_cost == pytest.approx(6.0)
    assert result.opportunity_cost == 0.0
    assert result.total_cost == pytest.approx(6.0)
    assert result.total_cost_bps == pytest.approx(150.0)


def test_implementation_shortfall_includes_unfilled_opportunity_cost() -> None:
    fills = (Fill("m1", "a1", 101.0, 6.0),)

    result = implementation_shortfall(
        fills,
        Side.BUY,
        arrival_price=100.0,
        target_quantity=10.0,
        final_price=103.0,
    )

    assert result.filled_quantity == 6.0
    assert result.unfilled_quantity == 4.0
    assert result.fill_rate == pytest.approx(0.6)
    assert result.execution_cost == pytest.approx(6.0)
    assert result.opportunity_cost == pytest.approx(12.0)
    assert result.total_cost == pytest.approx(18.0)
    assert result.total_cost_bps == pytest.approx(180.0)


def test_sell_shortfall_uses_sell_side_sign_convention() -> None:
    fills = (Fill("m1", "b1", 99.0, 4.0),)

    result = implementation_shortfall(
        fills,
        Side.SELL,
        arrival_price=100.0,
        target_quantity=10.0,
        final_price=97.0,
    )

    assert result.execution_cost == pytest.approx(4.0)
    assert result.opportunity_cost == pytest.approx(18.0)
    assert result.total_cost == pytest.approx(22.0)
    assert result.total_cost_bps == pytest.approx(220.0)


def test_partial_shortfall_requires_final_price() -> None:
    with pytest.raises(ValueError, match="final_price"):
        implementation_shortfall(
            (Fill("m1", "a1", 101.0, 2.0),),
            Side.BUY,
            arrival_price=100.0,
            target_quantity=3.0,
        )


def test_shortfall_rejects_overfilled_target() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        implementation_shortfall(
            (Fill("m1", "a1", 100.0, 4.0),),
            Side.BUY,
            arrival_price=100.0,
            target_quantity=3.0,
        )


def test_analytics_reject_empty_fills_and_invalid_reference() -> None:
    with pytest.raises(ValueError, match="at least one"):
        summarize_fills(())
    with pytest.raises(ValueError, match="reference_price"):
        slippage_bps((Fill("m1", "a1", 100.0, 1.0),), Side.BUY, 0.0)
