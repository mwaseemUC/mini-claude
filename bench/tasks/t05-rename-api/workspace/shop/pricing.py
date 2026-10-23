"""Pricing helpers."""


def line_total(item: dict) -> float:
    """Price of one order line: price * qty."""
    return item["price"] * item["qty"]


def calc_total(items: list[dict], tax_rate: float = 0.0) -> float:
    """Total for a list of order lines, with tax, rounded to cents.

    Each item is {"price": float, "qty": int}. calc_total is the single place
    where order totals are computed.
    """
    subtotal = sum(line_total(i) for i in items)
    return round(subtotal * (1 + tax_rate), 2)
