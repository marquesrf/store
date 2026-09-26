"""Default event handlers + bus wiring (composition point).

Each handler reacts to one event type. Here they just log; in a real system
they'd send a confirmation email, trigger restock, etc. Keeping them in one
place makes the full set of reactions to a domain event easy to see.
"""

from __future__ import annotations

import logging

from store.domain.events import DomainEvent, OrderPlaced, OutOfStock
from store.service_layer.messagebus import Handler, MessageBus

logger = logging.getLogger("store.events")


def log_order_placed(event: OrderPlaced) -> None:
    logger.info(
        "order_placed order_id=%s total_cents=%s currency=%s",
        event.order_id,
        event.total_cents,
        event.currency,
    )


def log_out_of_stock(event: OutOfStock) -> None:
    logger.warning(
        "out_of_stock sku=%s requested=%s available=%s",
        event.sku,
        event.requested,
        event.available,
    )


DEFAULT_HANDLERS: dict[type[DomainEvent], list[Handler]] = {
    OrderPlaced: [log_order_placed],
    OutOfStock: [log_out_of_stock],
}


def make_bus() -> MessageBus:
    return MessageBus(DEFAULT_HANDLERS)
