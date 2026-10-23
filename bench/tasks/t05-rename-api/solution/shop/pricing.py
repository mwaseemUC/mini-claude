"""Pricing helpers."""

import warnings


def line_total(item: dict) -> float:
    """Price of one order line: price * qty."""
    return item["price"] * item["qty"]


def order_total(items: list[dict], tax_rate: float = 0.0) -> float:
    """Total for a list of order lines, with tax, rounded to cents.

    Each item is {"price": float, "qty": int}. order_total is the single place
    where order totals are computed.
    """
    subtotal = sum(line_total(i) for i in items)
    return round(subtotal * (1 + tax_rate), 2)


def calc_total(items: list[dict], tax_rate: float = 0.0) -> float:
    """Deprecated alias for order_total."""
    warnings.warn(
        "calc_total is deprecated, use order_total",
        DeprecationWarning,
        stacklevel=2,
    )
    return order_total(items, tax_rate)
