from collections.abc import Callable, Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from store.adapters.orm import metadata
from store.adapters.sqlalchemy import SqlAlchemyUnitOfWork
from store.domain.exceptions import EmptyOrder
from store.domain.order import Order, OrderStatus
from store.service_layer.services import ItemInput, place_order


@pytest.fixture
def session_factory() -> Iterator[Callable[[], Session]]:
    # StaticPool + a single in-memory connection so every session in the test
    # shares one database (a fresh one per test = isolation).
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


def read_order(factory: Callable[[], Session], order_id: str) -> Order | None:
    with SqlAlchemyUnitOfWork(factory) as uow:
        return uow.orders.get(order_id)


def test_place_order_persists_and_reads_back(
    session_factory: Callable[[], Session],
) -> None:
    place_order(
        SqlAlchemyUnitOfWork(session_factory),
        "o-1",
        [ItemInput("abc", 2, 500), ItemInput("xyz", 1, 250)],
    )

    # A separate UoW/session proves it really hit the database, not just memory.
    got = read_order(session_factory, "o-1")
    assert got is not None
    assert got.status is OrderStatus.PAID
    assert got.total().amount_cents == 1250
    assert {str(line.sku) for line in got.lines} == {"ABC", "XYZ"}


def test_reading_back_a_stored_order_emits_no_events(
    session_factory: Callable[[], Session],
) -> None:
    place_order(
        SqlAlchemyUnitOfWork(session_factory), "o-1", [ItemInput("abc", 1, 500)]
    )
    got = read_order(session_factory, "o-1")
    assert got is not None
    assert got.pull_events() == []  # rehydration must not replay OrderPlaced


def test_failed_use_case_rolls_back(session_factory: Callable[[], Session]) -> None:
    with pytest.raises(EmptyOrder):
        place_order(SqlAlchemyUnitOfWork(session_factory), "o-1", [])
    assert read_order(session_factory, "o-1") is None


def test_get_missing_order_returns_none(
    session_factory: Callable[[], Session],
) -> None:
    assert read_order(session_factory, "nope") is None
