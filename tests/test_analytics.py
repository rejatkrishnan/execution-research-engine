import pytest

from execution_engine import Fill, Side, slippage_bps, summarize_fills


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


def test_analytics_reject_empty_fills_and_invalid_reference() -> None:
    with pytest.raises(ValueError, match="at least one"):
        summarize_fills(())
    with pytest.raises(ValueError, match="reference_price"):
        slippage_bps((Fill("m1", "a1", 100.0, 1.0),), Side.BUY, 0.0)
