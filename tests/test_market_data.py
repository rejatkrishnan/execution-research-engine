import pytest

from execution_engine import LimitOrderBook, MarketOrder, Order, Side
from execution_engine.market_data import BookEvent, replay


def test_replay_applies_add_market_and_cancel_events_in_order() -> None:
    book = LimitOrderBook()
    events = (
        BookEvent(1.0, "add", order=Order("a1", Side.SELL, 101.0, 2.0)),
        BookEvent(2.0, "add", order=Order("a2", Side.SELL, 102.0, 1.0)),
        BookEvent(3.0, "market", order=MarketOrder("m1", Side.BUY, 2.5)),
        BookEvent(4.0, "cancel", order_id="a2"),
    )

    results = replay(events, book)

    assert [len(result.fills) for result in results] == [0, 0, 2, 0]
    assert results[2].fills[0].maker_order_id == "a1"
    assert results[2].fills[1].maker_order_id == "a2"
    assert book.best_ask is None
    assert len(book) == 0


def test_replay_rejects_out_of_order_timestamps() -> None:
    events = (
        BookEvent(2.0, "add", order=Order("b1", Side.BUY, 99.0, 1.0)),
        BookEvent(1.0, "cancel", order_id="b1"),
    )

    with pytest.raises(ValueError, match="sorted by timestamp"):
        replay(events)


@pytest.mark.parametrize(
    "event",
    [
        BookEvent(0.0, "add", order=Order("b1", Side.BUY, 99.0, 1.0)),
        BookEvent(0.0, "market", order=MarketOrder("m1", Side.BUY, 1.0)),
        BookEvent(0.0, "cancel", order_id="b1"),
    ],
)
def test_supported_events_construct(event: BookEvent) -> None:
    assert event.timestamp == 0.0


def test_event_validation_rejects_missing_payloads() -> None:
    with pytest.raises(ValueError, match="requires order"):
        BookEvent(1.0, "add")
    with pytest.raises(ValueError, match="requires order_id"):
        BookEvent(1.0, "cancel")
