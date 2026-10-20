# CE returned-source evidence utilities

This fork adds standalone, offline utilities for evaluating Context Engine tool
responses. They correct problems found in Context Engine's separate adapter; they
are **not claims of bugs in upstream ContextBench**, and do not change upstream
metric definitions or its default evaluation pipeline.

- `toon.py` decodes the JSON-like TOON forms emitted by CE. Quoted tokens must be
  consumed completely; array counts and table widths must match. Literal control
  characters supported by the CE producer remain valid inside quoted values.
- `source_lines.py` credits only returned, nonblank lines that match a frozen
  checkout at the claimed coordinates. A path or a claimed range alone is not
  evidence that the agent saw the code. A mismatched line earns no credit; other
  matching lines in a partial excerpt remain eligible.

Source matching normalizes CRLF to LF and ignores leading/trailing ASCII spaces
and tabs to tolerate display indentation. Interior whitespace and all other
characters remain exact. Form-feed and Unicode line separators are characters,
not LF line boundaries. Missing or non-UTF-8 source receives no credit. This is
line-level evidence, not proof that a whole symbol was returned or understood.

## Use

Python 3.10+; standard library only:

```python
from contrib.ce_evidence.toon import loads
from contrib.ce_evidence.source_lines import verified_lines

reply = loads('results[1]{path,start_line,snippet}:\n  example.py,1,"x = 1"')
# Resolve and validate each row's path inside the pinned repository first.
lines = verified_lines("/path/to/frozen/repo/example.py", "x = 1", (1, 1))
```

The caller owns path containment, collection/snapshot identity, tool-error
handling, and interval merging. Keep location-only metrics separate from verified
source coverage. These utilities do not provide a complete agent-log adapter,
runner, statistical analysis, or a general-purpose TOON implementation.

## Verify

```sh
python3 contrib/ce_evidence/test_source_lines.py
python3 contrib/ce_evidence/test_toon.py
```

Tests use synthetic fixtures only, including eight language-shaped excerpts,
Unicode, partial windows, stale content, malformed framing and unavailable files.
No model calls, indexing, credentials, run transcripts or sampled gold are needed.

These additions are licensed under the repository's Apache-2.0 code license.
Upstream copyright and license files are preserved. This addition does not grant
new rights to datasets or third-party repository contents. It publishes no
benchmark results and establishes no accuracy, token, turn-count or latency win.
