import pytest
from hypothesis import given
from hypothesis import strategies as st

from store.domain.exceptions import (
    CurrencyMismatch,
    InvalidMoney,
    InvalidQuantity,
    InvalidSku,
)
from store.domain.value_objects import Money, Quantity, Sku


class TestMoney:
    def test_equal_by_value(self) -> None:
        assert Money(1000, "BRL") == Money(1000, "BRL")

    def test_different_currency_not_equal(self) -> None:
        assert Money(1000, "BRL") != Money(1000, "USD")

    def test_add_same_currency(self) -> None:
        assert Money(1000) + Money(250) == Money(1250)

    def test_subtract_same_currency(self) -> None:
        assert Money(1000) - Money(250) == Money(750)

    def test_multiply_by_int(self) -> None:
        assert Money(300) * 3 == Money(900) == 3 * Money(300)

    def test_ordering(self) -> None:
        assert Money(100) < Money(200)
        assert Money(200) >= Money(200)

    def test_cross_currency_add_raises(self) -> None:
        with pytest.raises(CurrencyMismatch):
            Money(100, "BRL") + Money(100, "USD")

    def test_cross_currency_subtract_raises(self) -> None:
        with pytest.raises(CurrencyMismatch):
            Money(100, "BRL") - Money(100, "USD")

    def test_cross_currency_compare_raises(self) -> None:
        with pytest.raises(CurrencyMismatch):
            _ = Money(100, "BRL") < Money(100, "USD")

    @pytest.mark.parametrize("currency", ["br", "BRLL", "brl", "12", ""])
    def test_invalid_currency_rejected(self, currency: str) -> None:
        with pytest.raises(InvalidMoney):
            Money(100, currency)

    @pytest.mark.parametrize("bad", [1.5, "100", True])
    def test_non_int_amount_rejected(self, bad: object) -> None:
        with pytest.raises(InvalidMoney):
            Money(bad)  # type: ignore[arg-type]

    @given(a=st.integers(), b=st.integers())
    def test_add_then_subtract_roundtrips(self, a: int, b: int) -> None:
        # Property: (m + n) - n == m for any value. Catches sign/overflow issues.
        m, n = Money(a), Money(b)
        assert (m + n) - n == m


class TestSku:
    def test_normalizes_to_upper_and_strips(self) -> None:
        assert Sku("  abc-1 ").value == "ABC-1"

    def test_equal_after_normalization(self) -> None:
        assert Sku("abc-1") == Sku("ABC-1")

    @pytest.mark.parametrize("bad", ["", "-abc", "a b", "abc!", "  "])
    def test_invalid_sku_rejected(self, bad: str) -> None:
        with pytest.raises(InvalidSku):
            Sku(bad)

    @given(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=12
        )
    )
    def test_alnum_always_valid(self, s: str) -> None:
        assert Sku(s).value == s.upper()


class TestQuantity:
    def test_add(self) -> None:
        assert Quantity(2) + Quantity(3) == Quantity(5)

    def test_subtract(self) -> None:
        assert Quantity(5) - Quantity(2) == Quantity(3)

    def test_subtract_below_one_raises(self) -> None:
        with pytest.raises(InvalidQuantity):
            Quantity(2) - Quantity(2)  # would reach 0

    @pytest.mark.parametrize("bad", [0, -1, -100])
    def test_non_positive_rejected(self, bad: int) -> None:
        with pytest.raises(InvalidQuantity):
            Quantity(bad)

    @pytest.mark.parametrize("bad", [1.0, "3", True])
    def test_non_int_rejected(self, bad: object) -> None:
        with pytest.raises(InvalidQuantity):
            Quantity(bad)  # type: ignore[arg-type]

    @given(
        a=st.integers(min_value=1, max_value=10_000),
        b=st.integers(min_value=1, max_value=10_000),
    )
    def test_addition_is_always_valid_and_sums(self, a: int, b: int) -> None:
        assert (Quantity(a) + Quantity(b)).value == a + b
