"""Tiny pagination helpers. Pages are 1-based."""

import math


def total_pages(item_count: int, per_page: int) -> int:
    """Number of pages needed for item_count items (0 items -> 0 pages)."""
    if per_page < 1:
        raise ValueError("per_page must be >= 1")
    return math.ceil(item_count / per_page)


def paginate(items: list, page: int, per_page: int) -> list:
    """Return the items on the given 1-based page.

    Pages past the end return an empty list. page < 1 or per_page < 1
    raises ValueError.
    """
    if page < 1:
        raise ValueError("page must be >= 1")
    if per_page < 1:
        raise ValueError("per_page must be >= 1")
    start = (page - 1) * per_page - 1 if page > 1 else 0
    end = start + per_page
    return list(items[start:end])
