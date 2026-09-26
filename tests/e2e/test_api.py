from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from store.adapters.orm import metadata
from store.adapters.sqlalchemy import SqlAlchemyUnitOfWork
from store.entrypoints.api import app, get_uow
from store.service_layer.ports import UnitOfWork


@pytest.fixture
def client() -> Iterator[TestClient]:
    # In-memory DB shared across requests, isolated per test.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def override_uow() -> UnitOfWork:
        return SqlAlchemyUnitOfWork(factory)

    app.dependency_overrides[get_uow] = override_uow
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def test_place_then_fetch_order(client: TestClient) -> None:
    resp = client.post(
        "/orders",
        json={
            "order_id": "o-1",
            "items": [
                {"sku": "abc", "quantity": 2, "unit_price_cents": 500},
                {"sku": "xyz", "quantity": 1, "unit_price_cents": 250},
            ],
        },
    )
    assert resp.status_code == 201

    got = client.get("/orders/o-1")
    assert got.status_code == 200
    body = got.json()
    assert body["status"] == "paid"
    assert body["total_cents"] == 1250
    assert {item["sku"] for item in body["items"]} == {"ABC", "XYZ"}


def test_empty_items_is_rejected_by_validation(client: TestClient) -> None:
    # Pydantic min_length=1 rejects before reaching the domain -> 422.
    resp = client.post("/orders", json={"order_id": "o-1", "items": []})
    assert resp.status_code == 422


def test_duplicate_order_id_conflicts(client: TestClient) -> None:
    payload = {
        "order_id": "o-1",
        "items": [{"sku": "abc", "quantity": 1, "unit_price_cents": 500}],
    }
    assert client.post("/orders", json=payload).status_code == 201
    assert client.post("/orders", json=payload).status_code == 409


def test_fetch_missing_order_returns_404(client: TestClient) -> None:
    assert client.get("/orders/nope").status_code == 404
