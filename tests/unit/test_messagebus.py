from store.domain.events import DomainEvent, OrderPlaced, OutOfStock
from store.domain.value_objects import Sku
from store.service_layer.messagebus import Handler, MessageBus


def test_dispatches_event_to_its_handler() -> None:
    seen: list[OrderPlaced] = []
    bus = MessageBus({OrderPlaced: [seen.append]})

    bus.handle([OrderPlaced("o-1", 1000, "BRL")])

    assert seen == [OrderPlaced("o-1", 1000, "BRL")]


def test_dispatches_to_multiple_handlers() -> None:
    calls: list[str] = []
    handlers: dict[type[DomainEvent], list[Handler]] = {
        OrderPlaced: [lambda e: calls.append("a"), lambda e: calls.append("b")]
    }
    bus = MessageBus(handlers)

    bus.handle([OrderPlaced("o-1", 1000, "BRL")])

    assert calls == ["a", "b"]


def test_routes_by_event_type() -> None:
    placed: list[DomainEvent] = []
    out: list[DomainEvent] = []
    bus = MessageBus({OrderPlaced: [placed.append], OutOfStock: [out.append]})

    bus.handle([OrderPlaced("o-1", 1000, "BRL"), OutOfStock(Sku("abc"), 5, 2)])

    assert len(placed) == 1
    assert len(out) == 1


def test_event_with_no_handler_is_ignored() -> None:
    bus = MessageBus({})
    bus.handle([OrderPlaced("o-1", 1000, "BRL")])  # must not raise
