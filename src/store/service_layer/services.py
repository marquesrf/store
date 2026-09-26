"""Use cases (service layer).

Services orchestrate the domain: they take primitives / DTOs, build domain
objects, drive the aggregate, and persist through a Unit of Work. No HTTP, no
ORM here — that stays at the edges. Domain exceptions propagate untouched so
the edge can map them to responses.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from store.domain.order import Order
from store.domain.value_objects import Money, Quantity, Sku
from store.service_layer.messagebus import MessageBus
from store.service_layer.ports import UnitOfWork

logger = logging.getLogger("store.service")


@dataclass(frozen=True, slots=True)
class ItemInput:
    """One requested line, as primitives crossing into the domain."""

    sku: str
    quantity: int
    unit_price_cents: int


def place_order(
    uow: UnitOfWork,
    order_id: str,
    items: list[ItemInput],
    currency: str = "BRL",
    bus: MessageBus | None = None,
) -> None:
    """Create an order from raw input, pay it, and persist — atomically.

    If a bus is given, recorded domain events are dispatched only after the
    transaction commits, so handlers never react to a change that rolled back.
    """
    with uow:
        order = Order(order_id=order_id, currency=currency)
        for item in items:
            order.add_line(
                Sku(item.sku),
                Quantity(item.quantity),
                Money(item.unit_price_cents, currency),
            )
        order.pay()
        uow.orders.add(order)
        uow.commit()
        # Structured key=value fields via %-args (lazy: only formatted if logged).
        logger.info(
            "order_placed order_id=%s total_cents=%s currency=%s items=%s",
            order.order_id,
            order.total().amount_cents,
            currency,
            len(order.lines),
        )
    if bus is not None:
        bus.handle(order.pull_events())
