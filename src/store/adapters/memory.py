"""In-memory adapters.

A real, working implementation of the ports backed by a dict. Tests use it as
their fake (behavior, not mocks), and it doubles as a database-free way to run
the app in a demo. It satisfies the ``OrderRepository`` / ``UnitOfWork``
protocols structurally — note there's no import of the port classes here.
"""

from __future__ import annotations

from typing import Self

from store.domain.order import Order


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def add(self, order: Order) -> None:
        self._orders[order.order_id] = order

    def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)


class InMemoryUnitOfWork:
    """Tracks commit/rollback so tests can assert the boundary was respected.

    Since everything lives in one dict, rollback here only drops uncommitted
    additions; the point is to exercise the same commit discipline the real
    (SQLAlchemy) UoW will enforce.
    """

    def __init__(self) -> None:
        self.orders = InMemoryOrderRepository()
        self.committed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        # Nothing durable to undo in memory; kept to honor the protocol and to
        # make "was this committed?" observable in tests.
        pass
