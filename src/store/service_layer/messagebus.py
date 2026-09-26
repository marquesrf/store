"""Message bus: routes domain events to their handlers.

Aggregates record events; the bus dispatches them after a use case commits, so
side effects (notifications, stock alerts) stay decoupled from the core rules.
Adding a reaction to an event means registering a handler — no change to the
domain or the service that emits it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from store.domain.events import DomainEvent

# Handlers take a concrete event subtype; the registry is keyed by event type,
# so the value is intentionally Callable[[Any], None] to sidestep the
# contravariance mismatch between a base-typed slot and subtype-typed handlers.
Handler = Callable[[Any], None]


class MessageBus:
    def __init__(self, handlers: dict[type[DomainEvent], list[Handler]]) -> None:
        self._handlers = handlers

    def handle(self, events: Iterable[DomainEvent]) -> None:
        for event in events:
            for handler in self._handlers.get(type(event), []):
                handler(event)
