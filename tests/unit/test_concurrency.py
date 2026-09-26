import asyncio

import pytest

from store.concurrency import fetch_prices


def test_fetches_all_prices_concurrently() -> None:
    result = asyncio.run(fetch_prices(["a", "bb", "ccc"]))
    assert result == {"a": 100, "bb": 200, "ccc": 300}


def test_one_failure_cancels_group_and_raises_exceptiongroup() -> None:
    # Structured concurrency: a single failing task surfaces as an
    # ExceptionGroup, and no partial result leaks out.
    with pytest.raises(ExceptionGroup) as exc_info:
        asyncio.run(fetch_prices(["a", "BAD", "ccc"]))
    assert any(isinstance(e, ValueError) for e in exc_info.value.exceptions)
