import pytest

from cart import Cart


def test_add_and_count():
    c = Cart()
    c.add("apple", 1.0, 2)
    assert c.count() == 2


def test_total_without_codes():
    c = Cart()
    c.add("pen", 2.5)
    assert c.total() == 2.5


def test_apply_code_discounts_total():
    c = Cart()
    c.add("book", 20.0)
    c.apply_code("SAVE10")
    assert c.total() == 18.0


def test_same_code_twice_rejected():
    c = Cart()
    c.apply_code("SAVE10")
    with pytest.raises(ValueError):
        c.apply_code("SAVE10")


def test_unknown_code_rejected():
    c = Cart()
    with pytest.raises(ValueError):
        c.apply_code("NOPE")


def test_empty_cart_total_is_zero():
    assert Cart().total() == 0.0
