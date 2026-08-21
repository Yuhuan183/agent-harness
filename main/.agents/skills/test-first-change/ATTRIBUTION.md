# Attribution — test-first-change

Derived from Matt Pocock's agent skills.

- **Source**: <https://github.com/mattpocock/skills>
- **Upstream skill**: `skills/engineering/tdd/SKILL.md` plus `tdd/tests.md` and
  `tdd/mocking.md`. The first version of this file said `references/tests.md`;
  they are not in a subdirectory, and the path was written from memory rather
  than from the tree.
- **Reviewed release**: `v1.2.3` (2026-08-06)
- **Reviewed commit**: `885e2ca4d842d139e9aef4e48d366c63cb1b8013` — the Claude
  marketplace pin resolved on 2026-08-17, not the release tag. The two disagree
  by twelve commits while the version string does not move, so the SHA is the
  only thing that identifies what was read.
- **Licence**: MIT, Copyright (c) 2026 Matt Pocock. Full text below.

Upstream's text is not vendored here. The first version of this file classified
from a same-day reading held in memory, and a 2026-08-17 re-fetch of the pinned
files found four sections that under-credited upstream. The classification below
is written against the fetched bytes, and the per-section disposition with
upstream's hashes is in `docs/research/upstream-distillation-ledger.md`. Named
rather than linked, like every other pointer in this skill: these files deploy
outside the repo, where no relative path reaches that tree. A recheck must
re-fetch upstream; re-reading this file is not a recheck.

## What was taken, and how

Upstream `tdd` is 38 lines and mostly an index: it outsources what makes a good
test to `tdd/tests.md`, mock boundaries to `tdd/mocking.md`, and
the seam vocabulary to a separate `codebase-design` skill. Distilling it is
therefore three decisions about who inherits each, not a rewrite of 38 lines.

**Substantial portions.**

1. **The tautological category** (`SKILL.md` → "Four ways an assertion cannot
   fail", items 1 and 2). Upstream names **one** category — an assertion that
   recomputes the expected value the way the code does, and therefore "passes by
   construction". Splitting that into two is local; the category itself, and the
   reason it matters, are upstream's. The first version of this file claimed
   upstream named both, which credited it with a distinction it does not draw.
2. **The independent source of truth** (`SKILL.md` → "Then", step 1). Upstream:
   *"Expected values must come from an independent source of truth — a known-good
   literal, a worked example, the spec."* Ours keeps the list and nearly the
   sentence. It was unlisted here until the 2026-08-17 re-fetch.
3. **The seam definition** (`SKILL.md` → "Seam, defined here", first paragraph).
   Upstream: *"the public boundary you test at: the interface where you observe
   behavior without reaching inside."* A close adaptation, not an original. The
   first version of this file said the section *"owes upstream nothing but the
   gap it left"*, which is the one direction the distillation plan says not to get
   wrong — and it was wrong because the classification was written from memory
   rather than against the file.
4. **"Refactoring is not part of the loop"** (`references/tuning.md` →
   Authority). Nearly verbatim from upstream's rules of the loop, and unlisted
   until the same re-fetch.
5. **The mock boundary** (`SKILL.md` → "Mocking"). Close in substance to
   `mocking.md`: mock what you neither own nor can run, never the thing under
   test, and treat "only testable with the failing path mocked out" as a finding
   rather than a workaround.

**Rewritten concepts.** Write the check before the implementation, watch it fail
before it passes, one behaviour per check, smallest change that turns it green,
and don't introduce a parallel test style are upstream's ideas in this repo's
words.

**Written locally, on top of upstream's one sentence.** The
reach-versus-observability split, and the list of what is not a seam. Upstream
defines a seam in one line and sends the agent to `codebase-design` for the rest
of the vocabulary — module, depth, adapter, leverage, locality. That skill is not
imported and was not read, so everything past the definition is local; the
definition itself is listed above as adapted.

**Every worked example is local.** `references/tuning.md` carries the good and
bad pairs. Upstream's are TypeScript and Jest; this repo verifies with Python
`unittest`, shell checks and markdown contract assertions. The concepts port and
the examples do not, so these were written from shapes this repo has actually
shipped rather than translated.

**Dropped.**

- **The hard seam block.** Upstream reads "Test only at pre-agreed seams …
  confirm them with the user. No test is written at an unconfirmed seam." That
  contradicts this project's standing rule against asking what the repo already
  answers, and the local incident behind this skill had an unambiguous seam that
  simply did not reach the result — confirming it with a human would have
  changed nothing. Replaced with: derive the seam from the code and the existing
  test layout, and ask only when two candidates would produce materially
  different checks and nothing on disk decides.
- The opening instruction to read `CONTEXT.md` and consult ADRs. This repo does
  not have those and the plan forbids creating them; `AGENTS.md` and
  `docs/architecture.md` already own that role.
- **`mocking.md`'s second half** — dependency injection and SDK-style interfaces,
  i.e. how to design something so it is easy to mock. That is a design concern
  rather than a testing criterion and sits outside this skill's boundary, but the
  first version dropped it without recording the judgement.
- **Upstream's vertical-slicing rule was dropped and has been restored.** Only
  its negative half survived the first pass ("do not write every check up front").
  The positive rule — one check, one implementation, each a tracer bullet
  answering what the last cycle taught — is upstream's and is now in "Then",
  step 3.

**Added, with no upstream counterpart.**

- *A seam must reach the observable result, not only the action you control.*
  Item 3 of the catalogue. Upstream's tautological category does not cover this
  shape — the assertion can be entirely true and still unrelated to the outcome.
  From a local 2026-08-17 incident.
- *Never seen red.* Item 4. Upstream gates on writing the test first, which
  implies it; stating it as its own failure mode is local, and it is there
  because a green that had never been red is the move a local incident made.
- **The gate's second clause** — failing because a function does not exist yet is
  a compile error, not an observed failure. Upstream says watch it fail; it does
  not distinguish absent behaviour from absent scaffolding.
- **One question for all four shapes**: what would I change to make this fail?
- An explicit authority split, and the pointer back to `evidence-debugging` for
  an unexplained defect. Upstream has no authority gate anywhere.

## Rechecking

`scripts/upstream-recheck.sh` re-fetches the pinned files and checks them
against the hashes the ledger was written against; the per-section disposition is
in `docs/research/upstream-distillation-ledger.md`. Start there.

Resolve the current marketplace pin before comparing — do not assume this SHA is
still what the marketplace serves, and fetch upstream rather than working from
this file. Compare `tdd/SKILL.md`, `tdd/tests.md` and `tdd/mocking.md`;
comparing only `SKILL.md` reads 38 lines of index and misses where the content
lives. Re-classify **every** section, not only the ones already listed here: the
failure this project has actually made is calling a substantial portion a
concept rewrite, and it is invisible to anyone who only checks the entries that
exist. Classify each upstream change as adopt / adapt / already-covered /
reject, reopen `references/tuning.md` before deciding, and advance the SHA above
only after the selected diff has been reviewed. A pin that moved is not by
itself a reason to follow it.

## MIT Licence

MIT License

Copyright (c) 2026 Matt Pocock

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
