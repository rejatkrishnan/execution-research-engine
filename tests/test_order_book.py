import pytest

from execution_engine import LimitOrderBook, Order, Side


def test_best_prices_and_spread() -> None:
    book = LimitOrderBook()
    book.add(Order("b1", Side.BUY, 99.0, 2.0))
    book.add(Order("b2", Side.BUY, 100.0, 1.0))
    book.add(Order("a1", Side.SELL, 102.0, 1.5))
    book.add(Order("a2", Side.SELL, 101.0, 1.0))

    assert book.best_bid == 100.0
    assert book.best_ask == 101.0
    assert book.spread == 1.0


def test_fifo_priority_within_price_level() -> None:
    book = LimitOrderBook()
    first = Order("b1", Side.BUY, 100.0, 1.0)
    second = Order("b2", Side.BUY, 100.0, 3.0)
    book.add(first)
    book.add(second)

    assert book.orders_at(Side.BUY, 100.0) == (first, second)
    assert book.level_quantity(Side.BUY, 100.0) == 4.0


def test_cancel_removes_empty_level() -> None:
    book = LimitOrderBook()
    book.add(Order("a1", Side.SELL, 101.0, 2.0))

    removed = book.cancel("a1")

    assert removed.order_id == "a1"
    assert book.best_ask is None
    assert len(book) == 0


def test_duplicate_order_id_is_rejected() -> None:
    book = LimitOrderBook()
    book.add(Order("b1", Side.BUY, 100.0, 1.0))

    with pytest.raises(ValueError, match="duplicate order_id"):
        book.add(Order("b1", Side.SELL, 101.0, 1.0))


@pytest.mark.parametrize(
    ("price", "quantity"),
    [(0.0, 1.0), (-1.0, 1.0), (100.0, 0.0), (100.0, -1.0)],
)
def test_order_rejects_nonpositive_values(price: float, quantity: float) -> None:
    with pytest.raises(ValueError):
        Order("x", Side.BUY, price, quantity)
