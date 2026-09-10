# Attribution — leaf-dispatch

`leaf-dispatch` is the Codex half of a distilled skill. Its rules come from the
same upstream as its Claude twin, `baton-dispatch`.

- **Source**: <https://github.com/cablate/baton>
- **Reviewed commit**:
  `0ab4d2ec5c69820001eeac2a12fab2c87fd3e943` (2026-07-16) — the same pin as the
  twin, and `test_contracts` keeps the two equal so advancing one advances both.
- **Licence**: MIT, Copyright (c) 2026 CabLate. Full text below — it is
  reproduced here rather than referenced because this directory deploys as
  its own copy under `~/.codex/skills/`, and MIT requires the notice to
  travel with the copy.

**The clause-by-clause analysis lives in one place**, in
[`main/claude/skills/baton-dispatch/ATTRIBUTION.md`](../../../claude/skills/baton-dispatch/ATTRIBUTION.md):
what was adopted, what was rewritten in this repo's words, what was dropped, and
the wording pass the licence cares about. Repeating it here would create a
second copy to keep true, and the analysis is identical because the two halves
carry the same rules.

## Why this file exists at all

The trail was one-directional. The twin's attribution describes the
Claude/Codex split, so a reader working inside `main/codex/` had no way to learn
these rules were distilled — the record was in the one directory they were not
looking at. `scripts/upstream-pin-report.py` was never blind (it reports
`cablate/baton` from the twin's file either way), so nothing was unwatched; what
was missing was discoverability from this side.

Traced 2026-09-08 as the sample for the plan's Q10, which asked how much work
one provenance trace costs before scheduling the remaining six.

## What is local, on this side

The twin's attribution lists "the Claude/Codex twin split including the no-Bash
rule for read-only roles" among the things written here with no upstream
counterpart. That covers the split itself. What this skill says about dispatch
shape, briefs, stops, fixed records, QC and verifier triggers is upstream's idea
in this repo's words, on the terms set out in the twin's file.

## Licence

```
MIT License

Copyright (c) 2026 CabLate

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
