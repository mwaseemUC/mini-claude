"""Write the data files as exact bytes (no newline translation, deterministic)."""

from pathlib import Path

DATA = {
    "users.txt": b"alice\nbob\ncarol\n",
    "prices.csv": b"item,price\napple,1.20\npear,0.95\n",
    "notes.txt": b"Remember: update the quarterly figures.\nNo trailing newline here",
    "config.ini": b"[main]\nretries = 3\nverbose = true\n",
}


def setup(workspace: Path, task_dir: Path) -> None:
    data_dir = Path(workspace) / "data"
    data_dir.mkdir(exist_ok=True)
    for name, content in DATA.items():
        (data_dir / name).write_bytes(content)
