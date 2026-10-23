"""Write users.csv the way a Windows client exports it: Windows-1252 bytes, CRLF line ends."""

from pathlib import Path

TEXT = (
    "id,name,email,note\r\n"
    "1,José Álvarez,jose@example.com,Prefers email\r\n"
    "2,Siobhán O’Brien,siobhan@example.com,Pays €40 monthly\r\n"
    "3,Zoë Müller,zoe@example.com,\r\n"
    "4,François “Frank” Dubois,frank@example.com,Plan – annual\r\n"
)


def setup(workspace: Path, task_dir: Path) -> None:
    data = TEXT.encode("cp1252")
    assert b"\x92" in data and b"\x80" in data
    (Path(workspace) / "users.csv").write_bytes(data)
