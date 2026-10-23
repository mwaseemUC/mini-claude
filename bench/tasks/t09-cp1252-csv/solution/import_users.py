"""Load users from the CSV the client sends us and print a short summary."""

import csv
import sys


def import_users(path: str) -> list[dict]:
    """Return one dict per row: id (int), name, email, note (all str).

    The client exports from Windows, so the file is Windows-1252, not UTF-8.
    """
    users = []
    with open(path, newline="", encoding="cp1252") as f:
        for row in csv.DictReader(f):
            users.append(
                {
                    "id": int(row["id"]),
                    "name": row["name"].strip(),
                    "email": row["email"].strip().lower(),
                    "note": row["note"].strip(),
                }
            )
    return users


def main(path: str = "users.csv") -> None:
    users = import_users(path)
    print(f"imported {len(users)} users")
    for u in users:
        print(f"{u['id']}: {u['name']} <{u['email']}>")


if __name__ == "__main__":
    main(*sys.argv[1:2])
