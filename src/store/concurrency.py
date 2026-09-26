"""Concurrency example: fetching data with asyncio.TaskGroup (3.11+).

A learning aside, not part of the request/response path. It shows *structured
concurrency*: ``TaskGroup`` starts several I/O-bound calls at once, waits for
all of them, and — crucially — if one fails it cancels the siblings and raises
an ``ExceptionGroup``. No leaked tasks, no silent partial results.

Run it directly: ``uv run python -m store.concurrency``.
"""

from __future__ import annotations

import asyncio


async def fetch_price(sku: str) -> tuple[str, int]:
    """Pretend to call a slow pricing service (async I/O)."""
    if sku == "BAD":
        raise ValueError("no price for BAD")
    await asyncio.sleep(0.01)  # stand-in for a network round-trip
    return sku, len(sku) * 100


async def fetch_prices(skus: list[str]) -> dict[str, int]:
    """Fetch every SKU's price concurrently and return them keyed by SKU.

    All fetches run in parallel; if any raises, TaskGroup cancels the rest and
    propagates an ExceptionGroup, so the caller never sees a half-filled dict.
    """
    async with asyncio.TaskGroup() as tg:
        tasks = {sku: tg.create_task(fetch_price(sku)) for sku in skus}
    # Reached only if all tasks succeeded.
    return {sku: task.result()[1] for sku, task in tasks.items()}


async def _demo() -> None:
    prices = await fetch_prices(["a", "bb", "ccc"])
    print("prices:", prices)


if __name__ == "__main__":
    asyncio.run(_demo())
