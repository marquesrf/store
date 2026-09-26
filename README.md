# store

A small order-management system built end to end as a study project, to
practice **modern Python** and **Domain-Driven Design**. The domain is
deliberately simple — a store with a catalog, orders, and stock — so the focus
stays on structure: keeping business rules pure and pushing frameworks to the
edges.

> Learning project. The goal is the shape of the code, not feature completeness.

## What it demonstrates

- **A pure domain.** Value objects (`Money`, `Sku`, `Quantity`), an `Order`
  aggregate that guards its own invariants, and domain events — with **zero
  imports** of any web or database framework.
- **Ports & adapters (hexagonal).** The service layer depends on `Protocol`
  interfaces; concrete adapters (in-memory and SQLAlchemy) plug in from the
  outside. The domain and use cases never learn how persistence or HTTP work.
- **Data-mapper persistence.** SQLAlchemy 2.0 Core tables with a repository
  that translates rows ↔ domain objects by hand, so the ORM never dictates the
  shape of the domain. Alembic manages migrations.
- **A thin HTTP edge.** FastAPI routes parse a Pydantic v2 request, call a
  service, and map domain errors to status codes — no business logic in the
  routes.
- **A message bus** that dispatches domain events to decoupled handlers after a
  use case commits.
- **Concurrency example** with `asyncio.TaskGroup` (structured concurrency).

## Architecture

```
entrypoints/     FastAPI adapter (HTTP)            depends on ↓
service_layer/   use cases, ports, message bus     depends on ↓
domain/          pure business rules (no deps)     ← everything points here
adapters/        in-memory + SQLAlchemy, ORM tables  implement the ports
```

Dependencies point inward only. Swapping the web framework or the database
touches the outer rings, never the core.

## Tech stack

Python 3.14 · [uv](https://docs.astral.sh/uv/) · [Ruff](https://docs.astral.sh/ruff/)
· mypy (strict) · pytest · SQLAlchemy 2.0 · Alembic · Pydantic v2 · FastAPI

## Getting started

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv sync                 # create the venv and install everything
uv run pytest           # run the test suite (unit / integration / e2e)
```

Run the database migrations and start the API:

```bash
uv run alembic upgrade head
uv run uvicorn store.entrypoints.api:app --reload
```

Then place and fetch an order:

```bash
curl -X POST localhost:8000/orders -H 'content-type: application/json' -d '{
  "order_id": "o-1",
  "items": [{"sku": "abc", "quantity": 2, "unit_price_cents": 500}]
}'

curl localhost:8000/orders/o-1
```

## Development

```bash
uv run ruff check       # lint
uv run ruff format      # format
uv run mypy             # type check (strict)
uv run pytest           # tests
uv run pre-commit install   # run the checks on every commit
```

## Docker

```bash
docker build -t store .
docker run -p 8000:8000 store
```

## Project layout

```
src/store/
  domain/          value objects, Order aggregate, events, stock
  service_layer/   use cases, ports (Protocol), message bus, handlers
  adapters/        in-memory + SQLAlchemy repositories, ORM tables
  entrypoints/     FastAPI app
tests/             unit / integration / e2e
migrations/        Alembic
docs/              PLAN, PROGRESS, NOTES (phase-by-phase log)
```

## License

MIT
