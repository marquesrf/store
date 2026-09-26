from store.domain.events import OrderPlaced, OutOfStock
from store.domain.order import Order
from store.domain.stock import StockItem
from store.domain.value_objects import Money, Quantity, Sku


class TestOrderEvents:
    def test_pay_records_order_placed(self) -> None:
        order = Order(order_id="o-1")
        order.add_line(Sku("abc"), Quantity(2), Money(500))
        order.pay()
        events = order.pull_events()
        assert events == [OrderPlaced(order_id="o-1", total_cents=1000, currency="BRL")]

    def test_pull_events_clears_them(self) -> None:
        order = Order(order_id="o-1")
        order.add_line(Sku("abc"), Quantity(1), Money(500))
        order.pay()
        order.pull_events()
        assert order.pull_events() == []  # already drained

    def test_open_order_has_no_events(self) -> None:
        order = Order(order_id="o-1")
        order.add_line(Sku("abc"), Quantity(1), Money(500))
        assert order.pull_events() == []


class TestStockEvents:
    def test_successful_allocation_reduces_stock_and_emits_nothing(self) -> None:
        item = StockItem(Sku("abc"), available=10)
        assert item.allocate(Quantity(3)) is True
        assert item.available == 7
        assert item.pull_events() == []

    def test_allocating_more_than_available_emits_out_of_stock(self) -> None:
        item = StockItem(Sku("abc"), available=2)
        assert item.allocate(Quantity(5)) is False
        assert item.available == 2  # unchanged
        assert item.pull_events() == [
            OutOfStock(sku=Sku("abc"), requested=5, available=2)
        ]
