import subprocess
import sys
from pathlib import Path

SCRIPT = Path.cwd() / "wordcount.py"

SAMPLE = "The cat sat.\nThe dog sat down!\n\nA cat?\n"


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        timeout=30,
    )


def sample(tmp_path, text=SAMPLE):
    p = tmp_path / "sample.txt"
    p.write_bytes(text.encode("utf-8"))
    return str(p)


def test_script_exists():
    assert SCRIPT.is_file()


def test_summary_only(tmp_path):
    r = run(sample(tmp_path))
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["lines: 4", "words: 9", "chars: 39"]


def test_lines_flag(tmp_path):
    r = run("--lines", sample(tmp_path))
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [
        "lines: 4",
        "words: 9",
        "chars: 39",
        "line 1: 3",
        "line 2: 4",
        "line 3: 0",
        "line 4: 2",
    ]


def test_top_tie_break_alphabetical(tmp_path):
    r = run("--top", "2", sample(tmp_path))
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [
        "lines: 4",
        "words: 9",
        "chars: 39",
        "top 2:",
        "cat: 2",
        "sat: 2",
    ]


def test_top_more_than_distinct(tmp_path):
    r = run("--top", "50", sample(tmp_path))
    lines = r.stdout.splitlines()
    assert lines[3] == "top 50:"
    assert lines[4:] == ["cat: 2", "sat: 2", "the: 2", "a: 1", "dog: 1", "down: 1"]


def test_both_flags_order_and_flag_position(tmp_path):
    path = sample(tmp_path)
    r = run(path, "--top", "1", "--lines")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [
        "lines: 4",
        "words: 9",
        "chars: 39",
        "line 1: 3",
        "line 2: 4",
        "line 3: 0",
        "line 4: 2",
        "top 1:",
        "cat: 2",
    ]


def test_punctuation_and_case_normalised(tmp_path):
    r = run("--top", "3", sample(tmp_path, '"Hello," hello! (HELLO) world.\n--- ???\n'))
    out = r.stdout.splitlines()
    assert out[:3] == ["lines: 2", "words: 6", "chars: 39"]
    # "---" keeps its dashes (only . , ; : ! ? " ' ( ) are stripped), "???" becomes empty and is ignored
    assert out[3:] == ["top 3:", "hello: 3", "---: 1", "world: 1"]


def test_unicode_chars_counted_as_characters(tmp_path):
    r = run(sample(tmp_path, "café crème\n"))
    assert r.stdout.splitlines() == ["lines: 1", "words: 2", "chars: 11"]


def test_missing_file(tmp_path):
    missing = str(tmp_path / "nope.txt")
    r = run(missing)
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.strip() == f"error: cannot read {missing}"


def test_bad_top_value(tmp_path):
    path = sample(tmp_path)
    assert run("--top", "0", path).returncode == 2
    assert run("--top", "abc", path).returncode == 2
