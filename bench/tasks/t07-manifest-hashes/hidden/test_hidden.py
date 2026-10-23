import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()

EXPECTED = {
    "data/config.ini": "3f8cf3db0342b9229ecaf1af06273ec1aecda2ff5672ae5a7809610104de59e3",
    "data/notes.txt": "24cb4c1cf482a363c27c9a736da5175b6358da41114e2a9a69f2a5ac8384402c",
    "data/prices.csv": "3959b7d55e98cdb60119d308aa1a71de2f55313cdb57fe7a6b2e55a77b8af0f7",
    "data/users.txt": "54e7fd617a3c08ae396cadd191b9e16db655b8c9e0832d35902f7d351b8cd191",
}


def test_data_files_unchanged():
    on_disk = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "data").rglob("*")
        if p.is_file()
    }
    assert on_disk == EXPECTED


def test_manifest_matches_recomputed_hashes():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["algorithm"] == "sha256"
    assert manifest["files"] == EXPECTED


def test_verify_script_passes_and_is_unmodified():
    r = subprocess.run(
        [sys.executable, "verify.py"], capture_output=True, text=True, cwd=ROOT, timeout=30
    )
    assert r.returncode == 0, r.stdout + r.stderr
    src = (ROOT / "verify.py").read_text(encoding="utf-8")
    assert "UNLISTED" in src and "MISMATCH" in src and "sha256_of" in src
