import pytest

from store.adapters.memory import InMemoryUnitOfWork
from store.domain.events import DomainEvent, OrderPlaced
from store.domain.exceptions import EmptyOrder
from store.domain.order import OrderStatus
from store.service_layer.messagebus import MessageBus
from store.service_layer.services import ItemInput, place_order


def test_place_order_persists_a_paid_order() -> None:
    uow = InMemoryUnitOfWork()
    place_order(uow, "o-1", [ItemInput("abc", 2, 500), ItemInput("xyz", 1, 250)])

    order = uow.orders.get("o-1")
    assert order is not None
    assert order.status is OrderStatus.PAID
    assert order.total().amount_cents == 1250


def test_place_order_commits() -> None:
    uow = InMemoryUnitOfWork()
    place_order(uow, "o-1", [ItemInput("abc", 1, 500)])
    assert uow.committed is True


def test_place_order_records_order_placed_event() -> None:
    uow = InMemoryUnitOfWork()
    place_order(uow, "o-1", [ItemInput("abc", 1, 500)])

    order = uow.orders.get("o-1")
    assert order is not None
    assert order.pull_events() == [OrderPlaced("o-1", total_cents=500, currency="BRL")]


def test_place_order_with_no_items_raises_and_does_not_commit() -> None:
    uow = InMemoryUnitOfWork()
    with pytest.raises(EmptyOrder):
        place_order(uow, "o-1", [])
    assert uow.committed is False


def test_place_order_dispatches_events_to_bus() -> None:
    seen: list[DomainEvent] = []
    bus = MessageBus({OrderPlaced: [seen.append]})

    place_order(InMemoryUnitOfWork(), "o-1", [ItemInput("abc", 1, 500)], bus=bus)

    assert seen == [OrderPlaced("o-1", total_cents=500, currency="BRL")]
