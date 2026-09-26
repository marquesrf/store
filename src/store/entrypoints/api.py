"""HTTP adapter (FastAPI).

Thin on purpose: routes parse a Pydantic request, call a service, and map the
outcome to HTTP. No business logic lives here — that stays in the domain and
service layer. Pydantic models are DTOs for the edge only; they never travel
inward. The Unit of Work is injected via ``Depends`` so tests can swap in an
in-memory database.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from store.adapters.sqlalchemy import SqlAlchemyUnitOfWork
from store.config import settings
from store.domain.exceptions import DomainError
from store.service_layer.handlers import make_bus
from store.service_layer.ports import UnitOfWork
from store.service_layer.services import ItemInput, place_order

# One engine per process; the session factory is what a UoW consumes.
_engine = create_engine(settings.database_url)
_session_factory: Callable[[], Session] = sessionmaker(bind=_engine)
_bus = make_bus()


def get_uow() -> UnitOfWork:
    """Dependency: a fresh Unit of Work per request. Overridden in tests."""
    return SqlAlchemyUnitOfWork(_session_factory)


class ItemPayload(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_price_cents: int = Field(ge=0)


class PlaceOrderRequest(BaseModel):
    order_id: str
    currency: str = "BRL"
    items: list[ItemPayload] = Field(min_length=1)


class OrderResponse(BaseModel):
    order_id: str
    status: str
    currency: str
    total_cents: int
    items: list[ItemPayload]


app = FastAPI(title="store")


@app.post("/orders", status_code=201)
def post_order(
    request: PlaceOrderRequest, uow: UnitOfWork = Depends(get_uow)
) -> dict[str, str]:
    items = [ItemInput(i.sku, i.quantity, i.unit_price_cents) for i in request.items]
    try:
        place_order(uow, request.order_id, items, request.currency, bus=_bus)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="order already exists") from None
    except DomainError as exc:
        # Any broken business rule is a bad request; the exception type names it.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"order_id": request.order_id}


@app.get("/orders/{order_id}")
def get_order(order_id: str, uow: UnitOfWork = Depends(get_uow)) -> OrderResponse:
    with uow:
        order = uow.orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return OrderResponse(
        order_id=order.order_id,
        status=order.status.value,
        currency=order.currency,
        total_cents=order.total().amount_cents,
        items=[
            ItemPayload(
                sku=str(line.sku),
                quantity=line.quantity.value,
                unit_price_cents=line.unit_price.amount_cents,
            )
            for line in order.lines
        ],
    )
