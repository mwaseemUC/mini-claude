"""Check every file in data/ against manifest.json. Exit 0 only if all match.

Each file is hashed as raw bytes. A file in data/ that is missing from the manifest,
or listed in the manifest but absent on disk, is also a failure.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    listed = manifest["files"]
    on_disk = {p.relative_to(ROOT).as_posix() for p in (ROOT / "data").rglob("*") if p.is_file()}
    bad = 0
    for name in sorted(set(listed) | on_disk):
        if name not in listed:
            print(f"UNLISTED {name}")
            bad += 1
        elif name not in on_disk:
            print(f"MISSING  {name}")
            bad += 1
        elif sha256_of(ROOT / name) != listed[name]:
            print(f"MISMATCH {name}")
            bad += 1
        else:
            print(f"ok       {name}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
