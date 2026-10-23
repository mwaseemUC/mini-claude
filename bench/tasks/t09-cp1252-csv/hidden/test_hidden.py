from pathlib import Path

from import_users import import_users

NAMES = [
    "José Álvarez",
    "Siobhán O’Brien",
    "Zoë Müller",
    "François “Frank” Dubois",
]


def test_client_file_names_exact():
    users = import_users("users.csv")
    assert [u["name"] for u in users] == NAMES
    assert [u["id"] for u in users] == [1, 2, 3, 4]
    assert users[1]["note"] == "Pays €40 monthly"
    assert users[2]["note"] == ""
    assert users[3]["note"] == "Plan – annual"


def test_input_file_not_modified():
    raw = Path("users.csv").read_bytes()
    assert b"\x92" in raw and b"\x80" in raw  # still the original Windows-1252 export


def test_other_cp1252_file(tmp_path):
    p = tmp_path / "other.csv"
    p.write_bytes("id,name,email,note\r\n9,Šarûnas ‘Sam’,S@X.COM,€5\r\n".encode("cp1252"))
    [u] = import_users(str(p))
    assert u == {"id": 9, "name": "Šarûnas ‘Sam’", "email": "s@x.com", "note": "€5"}
