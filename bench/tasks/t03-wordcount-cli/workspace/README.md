# wordcount

A tiny `wc`-like tool. Python 3.12, standard library only. The script is `wordcount.py`.

```
python wordcount.py [--lines] [--top N] PATH
```

`PATH` is a UTF-8 text file.

## Definitions

- **lines**: the number of items in `text.splitlines()`.
- **words**: whitespace-separated tokens (`text.split()`), counted as-is.
- **chars**: `len(text)` of the decoded text, newlines included.
- For `--top`, a word is a whitespace-separated token lowercased, with the characters
  `. , ; : ! ? " ' ( )` stripped from both ends of the token. Tokens that are empty after
  stripping are ignored.

## Output

Always starts with the summary, three lines:

```
lines: 4
words: 9
chars: 39
```

`--lines` appends one line per input line, `line N: K` where N is the 1-based line number and
K the number of words on that line (0 for blank lines):

```
line 1: 3
line 2: 4
line 3: 0
line 4: 2
```

`--top N` appends a header `top N:` followed by the N most frequent words, one per line as
`word: count`. Ordering is count descending, then word ascending (alphabetical). If there are
fewer than N distinct words, print them all (the header still says `top N:`).

```
top 2:
cat: 2
sat: 2
```

When both flags are given, the order is summary, then the `--lines` block, then the `--top` block.
No blank lines between blocks.

## Errors

- If `PATH` cannot be read, print `error: cannot read PATH` (PATH exactly as given) to stderr and
  exit with status 2. Nothing is printed to stdout.
- If `N` is less than 1 (or not an integer), print a message to stderr and exit with status 2.
- Success exits with status 0.

## Example

`sample.txt`:

```
The cat sat.
The dog sat down!

A cat?
```

`python wordcount.py --top 2 sample.txt` prints:

```
lines: 4
words: 9
chars: 39
top 2:
cat: 2
sat: 2
```
