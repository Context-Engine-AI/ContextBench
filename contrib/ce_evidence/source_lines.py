"""Attribute returned excerpts to matching lines of a frozen UTF-8 checkout."""

from pathlib import Path


def verified_lines(path: str, snippet: str, span: tuple[int, int | None]) -> list[tuple[int, int]]:
    """Return only nonblank matching lines at the claimed, inclusive coordinates.

    Ignore leading/trailing ASCII spaces and tabs (display indentation), and normalize
    CRLF to LF. Preserve every other character, including interior whitespace and
    form-feed. Do not search elsewhere in the file or infer omitted/blank-line coverage.
    """
    start, end = span
    if start < 1 or (end is not None and end < start):
        return []
    try:
        source = Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
    except (OSError, UnicodeDecodeError):
        return []  # Unavailable source cannot establish evidence.
    shown = snippet.replace("\r\n", "\n").split("\n")
    pairs = zip(shown, source[start - 1:end])
    return [(line, line) for line, (got, want) in enumerate(pairs, start)
            if got.strip() and got.strip(" \t") == want.strip(" \t")]
