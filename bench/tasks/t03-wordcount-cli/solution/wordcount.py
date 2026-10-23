"""wordcount: a tiny wc-like tool. See README.md."""

import argparse
import sys
from collections import Counter

STRIP = ".,;:!?\"'()"


def positive_int(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("N must be >= 1")
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wordcount")
    parser.add_argument("--lines", action="store_true")
    parser.add_argument("--top", type=positive_int, metavar="N")
    parser.add_argument("path")
    args = parser.parse_args(argv)  # argparse exits with status 2 on bad usage

    try:
        with open(args.path, encoding="utf-8", newline="") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        print(f"error: cannot read {args.path}", file=sys.stderr)
        return 2

    out = [
        f"lines: {len(text.splitlines())}",
        f"words: {len(text.split())}",
        f"chars: {len(text)}",
    ]
    if args.lines:
        for i, line in enumerate(text.splitlines(), start=1):
            out.append(f"line {i}: {len(line.split())}")
    if args.top is not None:
        counts = Counter()
        for token in text.split():
            word = token.lower().strip(STRIP)
            if word:
                counts[word] += 1
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[: args.top]
        out.append(f"top {args.top}:")
        out.extend(f"{w}: {c}" for w, c in ranked)
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
