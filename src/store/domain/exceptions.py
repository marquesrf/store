"""Domain exceptions.

Business-rule violations get their own types (not a bare ``ValueError``) so the
edge — API, CLI — can map them to meaningful responses, and so tests can assert
on *why* something failed rather than on an incidental message string.
"""


class DomainError(Exception):
    """Base for every domain rule violation."""


class InvalidMoney(DomainError):
    pass


class CurrencyMismatch(DomainError):
    """Operation between values of different currencies."""


class InvalidSku(DomainError):
    pass


class InvalidQuantity(DomainError):
    pass


class OrderNotModifiable(DomainError):
    """Attempt to change an order that is no longer open (paid or cancelled)."""


class EmptyOrder(DomainError):
    """Attempt to pay an order with no lines."""


class LineNotFound(DomainError):
    """Referenced order line does not exist."""
