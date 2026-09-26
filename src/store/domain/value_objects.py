"""Domain value objects.

Value objects are immutable and defined by their value: two ``Money`` of 10.00
BRL are the same money. They validate on construction, so an invalid value is
*impossible* to hold — the rest of the domain never has to check again.

``frozen=True`` enforces immutability; ``slots=True`` trims memory overhead and
forbids accidental attributes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

from store.domain.exceptions import (
    CurrencyMismatch,
    InvalidMoney,
    InvalidQuantity,
    InvalidSku,
)


@total_ordering
@dataclass(frozen=True, slots=True)
class Money:
    """Monetary value in minor units (cents), to avoid float error.

    Storing cents as ``int`` keeps arithmetic exact — ``0.1 + 0.2`` in float is
    not ``0.3``, but ``10 + 20`` cents is always ``30``. Operations across
    different currencies are a domain error, not silent coercion.
    """

    amount_cents: int
    currency: str = "BRL"

    def __post_init__(self) -> None:
        if not isinstance(self.amount_cents, int) or isinstance(
            self.amount_cents, bool
        ):
            raise InvalidMoney("amount_cents must be an int (cents)")
        if not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise InvalidMoney(
                f"invalid currency: {self.currency!r} (expected ISO 4217, e.g. BRL)"
            )

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(f"{self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.amount_cents + other.amount_cents, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.amount_cents - other.amount_cents, self.currency)

    def __mul__(self, factor: int) -> Money:
        if not isinstance(factor, int) or isinstance(factor, bool):
            raise InvalidMoney("Money can only be multiplied by an int")
        return Money(self.amount_cents * factor, self.currency)

    __rmul__ = __mul__

    def __lt__(self, other: Money) -> bool:
        self._same_currency(other)
        return self.amount_cents < other.amount_cents

    def __str__(self) -> str:
        return f"{self.amount_cents / 100:.2f} {self.currency}"


@dataclass(frozen=True, slots=True)
class Sku:
    """Stock Keeping Unit — the product code.

    Normalized to upper case: 'abc-1' and 'ABC-1' are the same SKU. The format
    is restricted to avoid ambiguous codes or codes with whitespace.
    """

    value: str

    _PATTERN = re.compile(r"[A-Z0-9][A-Z0-9-]*")

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not self._PATTERN.fullmatch(normalized):
            raise InvalidSku(
                f"invalid SKU: {self.value!r} "
                "(use letters/digits/hyphen, starting with a letter or digit)"
            )
        # frozen: normalization requires setting the attribute directly.
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Quantity:
    """Item quantity — always a positive integer.

    An order line with zero or negative quantity makes no sense in the domain,
    so it simply cannot come into existence.
    """

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise InvalidQuantity("quantity must be an int")
        if self.value < 1:
            raise InvalidQuantity(f"quantity must be >= 1, got {self.value}")

    def __add__(self, other: Quantity) -> Quantity:
        return Quantity(self.value + other.value)

    def __sub__(self, other: Quantity) -> Quantity:
        return Quantity(self.value - other.value)  # < 1 raises InvalidQuantity
