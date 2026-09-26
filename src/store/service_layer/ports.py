"""Ports: the interfaces the service layer depends on.

These are ``Protocol``s, so any concrete class with matching methods satisfies
them structurally — no base class to inherit. The in-memory adapter (tests,
demos) and the future SQLAlchemy adapter both fit without importing this file.
That inversion is what lets us test the service layer with no database.
"""

from __future__ import annotations

from typing import Protocol, Self

from store.domain.order import Order


class OrderRepository(Protocol):
    def add(self, order: Order) -> None: ...
    def get(self, order_id: str) -> Order | None: ...


class UnitOfWork(Protocol):
    """Transaction boundary. One use case = one ``with uow:`` block, one commit.

    Exiting without an explicit ``commit()`` rolls back, so a half-finished use
    case never leaks a partial write.
    """

    # Read-only property (not a bare attribute) so a concrete UoW may expose a
    # more specific repository type and still satisfy the protocol.
    @property
    def orders(self) -> OrderRepository: ...

    def __enter__(self) -> Self: ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
