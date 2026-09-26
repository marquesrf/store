"""Stock (inventory) — minimal, just enough to emit OutOfStock.

Full inventory management belongs to a later phase. For now this models one
thing: allocating more than is available doesn't blow up — it records an
``OutOfStock`` event for a handler (a later message bus) to react to.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from store.domain.events import DomainEvent, OutOfStock
from store.domain.value_objects import Quantity, Sku


@dataclass(slots=True)
class StockItem:
    sku: Sku
    available: int
    _events: list[DomainEvent] = field(default_factory=list)

    # ponytail: pull_events is duplicated with Order. If a third recorder shows
    # up, extract a shared EventRecorder base; two copies don't earn one yet.
    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def allocate(self, quantity: Quantity) -> bool:
        """Reserve stock. Returns True if allocated, False (+ event) if short."""
        if quantity.value > self.available:
            self._events.append(OutOfStock(self.sku, quantity.value, self.available))
            return False
        self.available -= quantity.value
        return True
