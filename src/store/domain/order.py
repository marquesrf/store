"""Order aggregate.

``Order`` is the aggregate root: the only way in. Callers never touch lines
directly — they go through methods that enforce the invariants (an order can
only be modified while open, can't be paid empty, all money shares one
currency). Centralizing the rules here means no caller can leave an order in
an invalid state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from store.domain.events import DomainEvent, OrderPlaced
from store.domain.exceptions import (
    CurrencyMismatch,
    EmptyOrder,
    LineNotFound,
    OrderNotModifiable,
)
from store.domain.value_objects import Money, Quantity, Sku


class OrderStatus(Enum):
    OPEN = "open"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class OrderLine:
    """A single product line. Immutable — quantity changes replace the line."""

    sku: Sku
    quantity: Quantity
    unit_price: Money

    @property
    def subtotal(self) -> Money:
        return self.unit_price * self.quantity.value


@dataclass(slots=True)
class Order:
    order_id: str
    currency: str = "BRL"
    status: OrderStatus = OrderStatus.OPEN
    _lines: dict[Sku, OrderLine] = field(default_factory=dict)
    _events: list[DomainEvent] = field(default_factory=list)

    @property
    def lines(self) -> tuple[OrderLine, ...]:
        """Read-only view: callers can inspect lines but not mutate the dict."""
        return tuple(self._lines.values())

    def pull_events(self) -> list[DomainEvent]:
        """Return recorded events and clear them, so the bus dispatches each once."""
        events = list(self._events)
        self._events.clear()
        return events

    def _require_open(self) -> None:
        if self.status is not OrderStatus.OPEN:
            raise OrderNotModifiable(f"order is {self.status.value}, cannot modify")

    def add_line(self, sku: Sku, quantity: Quantity, unit_price: Money) -> None:
        self._require_open()
        if unit_price.currency != self.currency:
            raise CurrencyMismatch(f"{unit_price.currency} vs order {self.currency}")
        existing = self._lines.get(sku)
        if existing is not None:
            # Adding an existing SKU increases its quantity. We keep the first
            # price seen. ponytail: fine for this domain; a real catalog would
            # re-price from a price list rather than trust the caller's price.
            quantity = existing.quantity + quantity
            unit_price = existing.unit_price
        self._lines[sku] = OrderLine(sku, quantity, unit_price)

    def remove_line(self, sku: Sku) -> None:
        self._require_open()
        if sku not in self._lines:
            raise LineNotFound(str(sku))
        del self._lines[sku]

    def total(self) -> Money:
        total = Money(0, self.currency)
        for line in self._lines.values():
            total += line.subtotal
        return total

    def pay(self) -> None:
        self._require_open()
        if not self._lines:
            raise EmptyOrder(self.order_id)
        self.status = OrderStatus.PAID
        total = self.total()
        self._events.append(
            OrderPlaced(self.order_id, total.amount_cents, total.currency)
        )

    def cancel(self) -> None:
        # Cancelling a paid order would be a refund flow, out of scope here.
        self._require_open()
        self.status = OrderStatus.CANCELLED
