"""Synthetic, offline tests: python contrib/ce_evidence/test_source_lines.py."""

import tempfile
from pathlib import Path

from source_lines import verified_lines


def test_matching_lines_preserve_multilanguage_text() -> None:
    excerpts = (
        "def f():\n    return '你好'",
        "fn f() -> i32 {\n    42\n}",
        "function f() {\n    return '😀';\n}",
        "function f(): number {\n    return 42;\n}",
        "func f() int {\n\treturn 42\n}",
        "int f() {\n    return 42;\n}",
        'public String f() {\n    return "Привет";\n}',
        "public int F() {\n    return 42;\n}",
    )
    with tempfile.TemporaryDirectory(prefix="source-lines-") as tree:
        path = Path(tree, "source")
        for excerpt in excerpts:
            path.write_bytes(("prefix\r\n" + excerpt.replace("\n", "\r\n") + "\r\nsuffix").encode())
            lines = excerpt.count("\n") + 1
            assert verified_lines(str(path), excerpt, (2, 100)) == [(i, i) for i in range(2, lines + 2)]


def test_only_matched_lines_inside_claimed_range_count() -> None:
    with tempfile.TemporaryDirectory(prefix="source-lines-") as tree:
        path = Path(tree, "source")
        path.write_text("header\n    alpha\n\n    beta\nfooter\n", encoding="utf-8")
        cases = (
            ("alpha\n\nbeta\nfooter", (2, 4), [(2, 2), (4, 4)]),
            ("alpha\n\nWRONG\nfooter", (2, 5), [(2, 2), (5, 5)]),
            ("\n \t\n", (2, None), []),
            ("alpha", (1, None), []),
            ("header", (0, None), []),
            ("alpha", (2, 1), []),
            ("footer", (999, None), []),
            (" alpha \t", (2, 2), [(2, 2)]),
        )
        for snippet, span, expected in cases:
            assert verified_lines(str(path), snippet, span) == expected


def test_controls_are_characters_not_line_separators() -> None:
    with tempfile.TemporaryDirectory(prefix="source-lines-") as tree:
        path = Path(tree, "source")
        for control in ("\f", "\v", "\r", "\u2028", "\u2029"):
            snippet = f'x = "a{control}b"\nreturn x'
            path.write_bytes(snippet.encode())
            assert verified_lines(str(path), snippet, (1, None)) == [(1, 1), (2, 2)]
            assert verified_lines(str(path), snippet.replace(control, ""), (1, 1)) == []


def test_unavailable_or_non_utf8_source_cannot_count() -> None:
    with tempfile.TemporaryDirectory(prefix="source-lines-") as tree:
        path = Path(tree, "source")
        assert verified_lines(str(path), "x", (1, 1)) == []
        path.write_bytes(b"x\xff")
        assert verified_lines(str(path), "x", (1, 1)) == []


def test_whitespace_only_controls_are_not_evidence() -> None:
    with tempfile.TemporaryDirectory(prefix="source-lines-") as tree:
        path = Path(tree, "source")
        path.write_bytes(b"\f\n\v\n\t\n")
        assert verified_lines(str(path), "\f\n\v\n\t\n", (1, None)) == []


if __name__ == "__main__":
    for name, fn in sorted(globals().copy().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
