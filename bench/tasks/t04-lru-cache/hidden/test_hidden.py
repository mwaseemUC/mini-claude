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


def test_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" not in c
    assert c.get("b") == 2
    assert len(c) == 1


def test_update_existing_key_refreshes_recency_and_value():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)  # a is now most recent; no eviction, size unchanged
    assert len(c) == 2
    c.put("c", 3)  # evicts b, not a
    assert c.get("a") == 10
    assert "b" not in c


def test_get_missing_returns_default():
    c = LRUCache(2)
    assert c.get("nope") is None
    assert c.get("nope", "fallback") == "fallback"
    c.put("k", None)
    assert c.get("k", "fallback") is None  # stored None is not a miss
    assert len(c) == 1  # a miss must not insert anything
