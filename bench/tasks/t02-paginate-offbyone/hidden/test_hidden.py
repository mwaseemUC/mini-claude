import pytest

from pagination import paginate, total_pages

ITEMS = list(range(1, 11))  # 1..10


def test_first_page():
    assert paginate(ITEMS, 1, 3) == [1, 2, 3]


def test_second_page_no_repeat():
    assert paginate(ITEMS, 2, 3) == [4, 5, 6]


def test_third_page():
    assert paginate(ITEMS, 3, 3) == [7, 8, 9]


def test_last_partial_page():
    assert paginate(ITEMS, 4, 3) == [10]


def test_past_the_end_is_empty():
    assert paginate(ITEMS, 5, 3) == []


def test_pages_partition_the_list():
    for per_page in (1, 2, 3, 4, 7, 10, 25):
        pages = [paginate(ITEMS, p, per_page) for p in range(1, total_pages(10, per_page) + 1)]
        assert [x for page in pages for x in page] == ITEMS


def test_does_not_return_alias_of_input():
    out = paginate(ITEMS, 1, 10)
    out.append(99)
    assert ITEMS[-1] == 10


def test_invalid_args():
    with pytest.raises(ValueError):
        paginate(ITEMS, 0, 3)
    with pytest.raises(ValueError):
        paginate(ITEMS, 1, 0)


def test_total_pages():
    assert total_pages(0, 3) == 0
    assert total_pages(10, 3) == 4
    assert total_pages(9, 3) == 3
