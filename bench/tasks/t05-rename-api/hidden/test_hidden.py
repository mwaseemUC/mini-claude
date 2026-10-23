import warnings

import pytest

from shop import pricing
from shop.invoice import render_invoice
from shop.orders import Order

ITEMS = [{"price": 10.0, "qty": 2}, {"price": 2.5, "qty": 3}]


def test_order_total_behaviour():
    assert pricing.order_total(ITEMS) == 27.5
    assert pricing.order_total(ITEMS, 0.1) == 30.25
    assert pricing.order_total([], 0.2) == 0.0


def test_alias_warns_and_matches():
    with pytest.warns(DeprecationWarning, match="order_total") as rec:
        result = pricing.calc_total(ITEMS, 0.1)
    assert result == pricing.order_total(ITEMS, 0.1)
    assert rec[0].filename == __file__  # stacklevel=2 points at the caller


def test_alias_default_tax_rate():
    with pytest.warns(DeprecationWarning):
        assert pricing.calc_total(ITEMS) == 27.5


def test_alias_importable_by_name():
    from shop.pricing import calc_total

    with pytest.warns(DeprecationWarning):
        calc_total(ITEMS)


def test_public_paths_emit_no_deprecation_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        order = Order("Ada", tax_rate=0.1)
        order.add("pen", 2.5, 4)
        order.add("book", 10.0)
        assert order.total() == 22.0
        text = render_invoice(order)
    assert text.splitlines() == [
        "Invoice for Ada",
        "  pen x4 @ 2.50",
        "  book x1 @ 10.00",
        "Subtotal: 20.00",
        "Total: 22.00",
    ]
