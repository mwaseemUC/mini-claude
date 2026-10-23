import subprocess
import sys
from pathlib import Path

import pytest

from cart import Cart


def test_default_carts_do_not_share_items():
    a, b = Cart(), Cart()
    a.add("x", 1.0)
    assert b.items == []
    assert b.count() == 0
    assert Cart().items == []


def test_default_carts_do_not_share_codes():
    a, b = Cart(), Cart()
    a.apply_code("SAVE10")
    b.apply_code("SAVE10")  # must not raise: separate carts
    c = Cart()
    c.add("y", 100.0)
    assert c.total() == 100.0


def test_codes_stack_per_cart():
    c = Cart()
    c.add("z", 100.0)
    c.apply_code("SAVE10")
    c.apply_code("HALF")
    assert c.total() == 45.0
    assert Cart().applied_codes == []


def test_explicit_items_still_work():
    c = Cart([{"name": "a", "price": 3.0, "qty": 2}])
    assert c.total() == 6.0
    assert Cart().count() == 0


def test_visible_suite_passes_when_run_together():
    tests = Path.cwd() / "tests"
    assert tests.is_dir()
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tests)],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        timeout=60,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert " passed" in r.stdout and " failed" not in r.stdout  # extra regression tests are fine


@pytest.mark.parametrize("n", range(3))
def test_repeated_construction_is_clean(n):
    c = Cart()
    c.add("p", 1.0)
    c.apply_code("SAVE10")
    assert c.count() == 1
