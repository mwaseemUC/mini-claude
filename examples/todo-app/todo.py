import json
import sys
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent / "todos.json"


def load(path=DEFAULT_FILE):
    path = Path(path)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save(todos, path=DEFAULT_FILE):
    Path(path).write_text(json.dumps(todos, indent=2), encoding="utf-8")


def add(text, path=DEFAULT_FILE):
    todos = load(path)
    new_id = max((t["id"] for t in todos), default=0) + 1
    todo = {"id": new_id, "text": text, "done": False}
    todos.append(todo)
    save(todos, path)
    return todo


def mark_done(todo_id, path=DEFAULT_FILE):
    todos = load(path)
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            save(todos, path)
            return True
    return False


def remove(todo_id, path=DEFAULT_FILE):
    todos = load(path)
    rest = [t for t in todos if t["id"] != todo_id]
    if len(rest) == len(todos):
        return False
    save(rest, path)
    return True


def main(argv=None, path=DEFAULT_FILE):
    argv = sys.argv[1:] if argv is None else argv
    usage = "usage: todo.py add <text> | list | done <id> | remove <id>"
    if not argv:
        print(usage)
        return 1
    cmd, args = argv[0], argv[1:]
    if cmd == "add" and args:
        t = add(" ".join(args), path)
        print(f"Added {t['id']}: {t['text']}")
    elif cmd == "list" and not args:
        todos = load(path)
        if not todos:
            print("No todos.")
        for t in todos:
            print(f"{t['id']} [{'x' if t['done'] else ' '}] {t['text']}")
    elif cmd in ("done", "remove") and len(args) == 1 and args[0].isdigit():
        i = int(args[0])
        ok = mark_done(i, path) if cmd == "done" else remove(i, path)
        if not ok:
            print(f"No todo with id {i}")
            return 1
        print(f"{'Completed' if cmd == 'done' else 'Removed'} {i}")
    else:
        print(usage)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
