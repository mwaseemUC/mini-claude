import pytest

from cache import LRUCache


def test_put_and_get():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1


def test_len_counts_entries():
    c = LRUCache(3)
    assert len(c) == 0
    c.put("a", 1)
    c.put("b", 2)
    assert len(c) == 2


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert "a" not in c
    assert c.get("b") == 2
    assert c.get("c") == 3
    assert len(c) == 2


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)
    assert "a" in c
    assert "b" not in c


def test_invalid_capacity():
    with pytest.raises(ValueError):
        LRUCache(0)
