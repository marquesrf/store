import pytest

from store.domain.exceptions import (
    CurrencyMismatch,
    EmptyOrder,
    LineNotFound,
    OrderNotModifiable,
)
from store.domain.order import Order, OrderStatus
from store.domain.value_objects import Money, Quantity, Sku


def make_order() -> Order:
    return Order(order_id="o-1", currency="BRL")


class TestAddLine:
    def test_adds_a_line(self) -> None:
        order = make_order()
        order.add_line(Sku("abc"), Quantity(2), Money(500))
        assert len(order.lines) == 1
        assert order.lines[0].subtotal == Money(1000)

    def test_same_sku_merges_quantity_keeping_first_price(self) -> None:
        order = make_order()
        order.add_line(Sku("abc"), Quantity(2), Money(500))
        order.add_line(Sku("abc"), Quantity(3), Money(999))  # price ignored on merge
        assert len(order.lines) == 1
        assert order.lines[0].quantity == Quantity(5)
        assert order.lines[0].unit_price == Money(500)

    def test_rejects_line_in_different_currency(self) -> None:
        order = make_order()
        with pytest.raises(CurrencyMismatch):
            order.add_line(Sku("abc"), Quantity(1), Money(500, "USD"))

    def test_cannot_add_to_paid_order(self) -> None:
        order = make_order()
        order.add_line(Sku("abc"), Quantity(1), Money(500))
        order.pay()
        with pytest.raises(OrderNotModifiable):
            order.add_line(Sku("xyz"), Quantity(1), Money(200))


class TestRemoveLine:
    def test_removes_a_line(self) -> None:
        order = make_order()
        order.add_line(Sku("abc"), Quantity(1), Money(500))
        order.remove_line(Sku("abc"))
        assert order.lines == ()

    def test_removing_missing_line_raises(self) -> None:
        order = make_order()
        with pytest.raises(LineNotFound):
            order.remove_line(Sku("nope"))


class TestTotal:
    def test_empty_order_total_is_zero(self) -> None:
        assert make_order().total() == Money(0)

    def test_sums_subtotals(self) -> None:
        order = make_order()
        order.add_line(Sku("abc"), Quantity(2), Money(500))  # 1000
        order.add_line(Sku("xyz"), Quantity(1), Money(250))  # 250
        assert order.total() == Money(1250)


class TestPay:
    def test_pay_marks_order_paid(self) -> None:
        order = make_order()
        order.add_line(Sku("abc"), Quantity(1), Money(500))
        order.pay()
        assert order.status is OrderStatus.PAID

    def test_cannot_pay_empty_order(self) -> None:
        with pytest.raises(EmptyOrder):
            make_order().pay()

    def test_cannot_pay_twice(self) -> None:
        order = make_order()
        order.add_line(Sku("abc"), Quantity(1), Money(500))
        order.pay()
        with pytest.raises(OrderNotModifiable):
            order.pay()


class TestCancel:
    def test_cancel_marks_cancelled(self) -> None:
        order = make_order()
        order.cancel()
        assert order.status is OrderStatus.CANCELLED

    def test_cannot_cancel_paid_order(self) -> None:
        order = make_order()
        order.add_line(Sku("abc"), Quantity(1), Money(500))
        order.pay()
        with pytest.raises(OrderNotModifiable):
            order.cancel()
