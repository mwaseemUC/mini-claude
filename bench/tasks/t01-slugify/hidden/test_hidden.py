import pytest

from slugify import slugify


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Hello, World!", "hello-world"),
        ("  --Hello___World--  ", "hello-world"),
        ("Crème Brûlée à la façon", "creme-brulee-a-la-facon"),
        ("naïve café", "naive-cafe"),
        ("Price: 5€ only", "price-5-only"),
        ("a€b", "ab"),
        ("Python 3.12 -- what's new?", "python-3-12-what-s-new"),
        ("!!!", ""),
        ("", ""),
        ("ＦＵＬＬ width", "full-width"),
    ],
)
def test_basic(text, expected):
    assert slugify(text) == expected


def test_truncate_back_to_word_boundary():
    text = "the quick brown fox jumps over the lazy dog and cat"
    assert slugify(text) == "the-quick-brown-fox-jumps-over-the-lazy-dog-and"


def test_truncate_exactly_on_boundary_keeps_full_head():
    assert slugify("a" * 50 + " bbb") == "a" * 50


def test_truncate_single_long_word_hard_cut():
    assert slugify("a" * 60) == "a" * 50


def test_cut_lands_inside_word_after_dash_at_end_of_head():
    # slug is 49 a's, "-", "bbb": head ends with "-", next char is a letter.
    assert slugify("a" * 49 + " bbb") == "a" * 49


def test_exact_length_not_truncated():
    s = "a" * 25 + " " + "b" * 24
    assert len(slugify(s)) == 50
    assert slugify(s) == "a" * 25 + "-" + "b" * 24


def test_custom_max_length():
    assert slugify("hello wonderful world", max_length=14) == "hello"
    assert slugify("hello wonderful world", max_length=15) == "hello-wonderful"
    assert slugify("hello wonderful world", max_length=16) == "hello-wonderful"
    assert slugify("hello wonderful world", max_length=5) == "hello"
    assert slugify("hello wonderful world", max_length=3) == "hel"
