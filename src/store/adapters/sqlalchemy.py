"""SQLAlchemy adapters: repository + unit of work (data-mapper style).

The repository hand-translates between rows and domain objects using
SQLAlchemy 2.0 Core (`select`/`insert`). The Unit of Work owns the session and
the transaction boundary: one `with uow:` block, one `commit()`, and a
rollback if the block leaves without committing.

Both classes satisfy the `service_layer.ports` protocols structurally, so the
service layer never learns this file exists.
"""

from __future__ import annotations

from collections.abc import Callable

import sqlalchemy as sa
from sqlalchemy.orm import Session

from store.adapters.orm import order_lines, orders
from store.domain.order import Order, OrderStatus
from store.domain.value_objects import Money, Quantity, Sku


class SqlAlchemyOrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, order: Order) -> None:
        self._session.execute(
            sa.insert(orders).values(
                order_id=order.order_id,
                currency=order.currency,
                status=order.status.value,
            )
        )
        for line in order.lines:
            self._session.execute(
                sa.insert(order_lines).values(
                    order_id=order.order_id,
                    sku=str(line.sku),
                    quantity=line.quantity.value,
                    unit_price_cents=line.unit_price.amount_cents,
                )
            )

    def get(self, order_id: str) -> Order | None:
        row = self._session.execute(
            sa.select(orders).where(orders.c.order_id == order_id)
        ).one_or_none()
        if row is None:
            return None

        # Rehydrate through the domain: build OPEN, add lines, then restore the
        # persisted status directly. We bypass pay() on purpose — replaying a
        # stored order must not re-emit OrderPlaced.
        order = Order(order_id=row.order_id, currency=row.currency)
        line_rows = self._session.execute(
            sa.select(order_lines).where(order_lines.c.order_id == order_id)
        )
        for lr in line_rows:
            order.add_line(
                Sku(lr.sku),
                Quantity(lr.quantity),
                Money(lr.unit_price_cents, row.currency),
            )
        order.status = OrderStatus(row.status)
        return order


class SqlAlchemyUnitOfWork:
    orders: SqlAlchemyOrderRepository

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self.committed = False

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.orders = SqlAlchemyOrderRepository(self._session)
        self.committed = False
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()
        self.committed = True

    def rollback(self) -> None:
        self._session.rollback()
