import pytest

import todo


@pytest.fixture
def p(tmp_path):
    return tmp_path / "todos.json"


def test_add_and_list(p, capsys):
    assert todo.main(["add", "buy", "milk"], p) == 0
    assert todo.main(["list"], p) == 0
    out = capsys.readouterr().out
    assert "1 [ ] buy milk" in out


def test_done(p, capsys):
    todo.main(["add", "a"], p)
    assert todo.main(["done", "1"], p) == 0
    assert todo.load(p)[0]["done"] is True


def test_remove_keeps_ids_unique(p):
    todo.main(["add", "a"], p)
    todo.main(["add", "b"], p)
    assert todo.main(["remove", "1"], p) == 0
    todo.main(["add", "c"], p)
    assert [t["id"] for t in todo.load(p)] == [2, 3]


def test_missing_id(p, capsys):
    assert todo.main(["done", "5"], p) == 1
    assert todo.main(["remove", "5"], p) == 1


def test_bad_usage(p):
    assert todo.main([], p) == 1
    assert todo.main(["add"], p) == 1
    assert todo.main(["done", "x"], p) == 1


def test_empty_list(p, capsys):
    todo.main(["list"], p)
    assert "No todos" in capsys.readouterr().out
