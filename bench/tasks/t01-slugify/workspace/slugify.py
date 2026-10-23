"""URL slug helper."""


def slugify(text: str, max_length: int = 50) -> str:
    """Turn arbitrary text into a URL slug.

    Rules, applied in this order:

    1. Unicode-normalize with NFKD, then drop every character that is not ASCII
       (so "Crème Brûlée" becomes "Creme Brulee"; a character with no ASCII
       decomposition, such as the euro sign, is simply dropped).
    2. Lowercase.
    3. Replace every run of one or more characters that are not in a-z or 0-9
       with a single "-".
    4. Strip leading and trailing "-".
    5. If the slug is longer than max_length, truncate it without cutting a word
       in half where possible:
         - Take the first max_length characters.
         - If the character right after that cut is "-", the cut already falls
           on a word boundary: keep the first max_length characters.
         - Otherwise, cut back to the last "-" inside the first max_length
           characters and drop that "-" and everything after it.
         - If there is no "-" in the first max_length characters (one very long
           word), hard-cut at exactly max_length characters.
       Finally strip any trailing "-" from the result.

    An input with no letters or digits returns "".
    """
    raise NotImplementedError
