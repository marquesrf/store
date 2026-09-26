"""Domain events.

A domain event is an immutable fact: something that already happened
(an order was placed, a SKU went out of stock). Aggregates *record* events as
they change state; a message bus dispatches them later (see T3.1). Keeping them
as plain frozen dataclasses means the domain stays free of any messaging
framework — the event is just data.
"""

from __future__ import annotations

from dataclasses import dataclass

from store.domain.value_objects import Sku


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base marker for domain events."""


@dataclass(frozen=True, slots=True)
class OrderPlaced(DomainEvent):
    order_id: str
    total_cents: int
    currency: str


@dataclass(frozen=True, slots=True)
class OutOfStock(DomainEvent):
    sku: Sku
    requested: int
    available: int
