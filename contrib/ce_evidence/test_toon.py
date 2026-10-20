#!/usr/bin/env python3
"""TOON framing regressions. Run: python contrib/ce_evidence/test_toon.py."""
import json

import toon


def _assert_rejected(doc: str) -> None:
    try:
        toon.loads(doc)
    except ValueError:
        return
    raise AssertionError(f"malformed TOON accepted: {doc!r}")


def test_quoted_scalar_rejects_suffix() -> None:
    for value in ('"code"garbage', '"code" "more"', '"code",tail'):
        _assert_rejected(f"snippet: {value}")
        _assert_rejected(f"results[1]:\n  - snippet: {value}")
        _assert_rejected(f"values[1]:\n  - {value}")


def test_scalar_rejects_unmatched_quotes() -> None:
    for value in ('"unterminated', 'bare"quote', 'bare "quoted"'):
        _assert_rejected(f"snippet: {value}")


def test_rows_reject_garbage_after_quotes() -> None:
    for row in ('"code"garbage,tail', '"code" "more",tail', 'one,"code"garbage'):
        _assert_rejected(f"values[2]: {row}")
        _assert_rejected(f"rows[1]{{snippet,path}}:\n  {row}")


def test_rows_reject_empty_unquoted_fields() -> None:
    for row in (',tail', 'head,', ','):
        _assert_rejected(f"values[2]: {row}")
        _assert_rejected(f"rows[1]{{snippet,path}}:\n  {row}")
    _assert_rejected("values[3]: one,,three")


def test_inline_arrays_require_declared_count() -> None:
    for doc in ("values[2]: one", "values[1]: one,two", "values[0]: one"):
        _assert_rejected(doc)


def test_list_arrays_require_declared_count() -> None:
    for doc in (
        "values[1]:", "values[2]:\n  - one", "values[0]:\n  - one",
        "values[1]:\n  - one\n  - two",
        "results[2]:\n  - path: one\n    snippet: code",
        "results[1]:\n  - path: one\n  - path: two",
        "outer:\n  values[2]:\n    - one\n  next: value",
    ):
        _assert_rejected(doc)


def test_tabular_arrays_require_declared_count() -> None:
    for doc in (
        "rows[1]{path}:", "rows[2]{path}:\n  one", "rows[0]{path}:\n  one",
        "rows[1]{path}:\n  one\n  two",
        "rows[2]{path}:\n  one\nnext: value",
    ):
        _assert_rejected(doc)


def test_tabular_arrays_require_exact_width() -> None:
    for row in ("one", "one,two,three"):
        _assert_rejected(f"rows[1]{{path,snippet}}:\n  {row}")


def test_tabular_headers_reject_ignored_content() -> None:
    for doc in (
        "rows[1]{path}: ignored\n  one", "rows[0]{path}: ignored", "rows{path}: one",
        'rows[1]{"path"garbage}:\n  one', "rows[1]{path,}:\n  one",
    ):
        _assert_rejected(doc)


def test_array_rows_require_consistent_indentation() -> None:
    _assert_rejected("values[2]:\n  - one\n    - two")
    _assert_rejected("rows[2]{path}:\n  one\n    two")


def test_literal_controls_survive_in_quoted_values() -> None:
    for control in ("\f", "\v", "\b", "\x00", "\x1f"):
        value = f"before{control}:after"
        quoted = f'"{value}"'
        assert toon.loads(f"snippet: {quoted}") == {"snippet": value}
        assert toon.loads(f"values[1]: {quoted}") == {"values": [value]}
        assert toon.loads(f"rows[1]{{snippet}}:\n  {quoted}") == {"rows": [{"snippet": value}]}
        _assert_rejected(f"values[1]: {quoted}garbage")


def test_quoted_strings_preserve_unicode_commas_and_escapes() -> None:
    value = 'λ, "quoted" \\path\nnext\tline'
    quoted = json.dumps(value, ensure_ascii=False)
    doc = f"snippet: {quoted}\nvalues[2]: {quoted},\"\"\nrows[1]{{snippet,path}}:\n  {quoted},\"\""
    assert toon.loads(doc) == {
        "snippet": value, "values": [value, ""], "rows": [{"snippet": value, "path": ""}],
    }


def test_quoted_table_keys_preserve_commas_and_escapes() -> None:
    keys = ['λ,field', '"quoted"', '\\path', 'true', '123']
    fields = ",".join(json.dumps(key, ensure_ascii=False) for key in keys)
    assert toon.loads(f"rows[1]{{{fields}}}:\n  1,2,3,4,5") == {
        "rows": [dict(zip(keys, [1, 2, 3, 4, 5]))],
    }


def test_all_existing_container_forms_remain_supported() -> None:
    doc = ('ok: true\nempty:\nvalues[0]:\nempty_rows[0]{path,snippet}:\n'
           'nested:\n  values[3]: 1,false,null\n'
           'results[2]:\n  - path: one.py\n    source:\n      start: 1\n'
           '    lines[2]:\n      - first\n      - second\n  - path: two.py\n'
           'rows[1]{path,snippet}:\n  one.py,"a, b"\nnext: done')
    assert toon.loads(doc) == {
        "ok": True, "empty": {}, "values": [], "empty_rows": [],
        "nested": {"values": [1, False, None]},
        "results": [
            {"path": "one.py", "source": {"start": 1}, "lines": ["first", "second"]},
            {"path": "two.py"},
        ],
        "rows": [{"path": "one.py", "snippet": "a, b"}], "next": "done",
    }


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
