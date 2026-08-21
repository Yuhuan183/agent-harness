# Attribution — evidence-debugging

Derived from Matt Pocock's agent skills.

- **Source**: <https://github.com/mattpocock/skills>
- **Upstream skill**: `skills/engineering/diagnosing-bugs/SKILL.md`
- **Reviewed release**: `v1.2.3` (2026-08-06)
- **Reviewed commit**: `885e2ca4d842d139e9aef4e48d366c63cb1b8013` — the Claude
  marketplace pin resolved on 2026-08-17, not the release tag. The two disagree
  by twelve commits while the version string does not move, so the SHA is the
  only thing that identifies what was read.
- **Licence**: MIT, Copyright (c) 2026 Matt Pocock. Full text below.

## What was taken, and how

**Substantial portions — two sections, not one.**

1. **The Phase 1 completion criterion** (`SKILL.md` → "The gate"). A close
   adaptation, deliberately: the value is in the precision of the wording —
   *already run at least once*, *red-capable*, *asserts the symptom the user
   described*, *not "runs without erroring"*, and the instruction to stop when a
   theory arrives before the command does. Paraphrasing weakens it. The four
   criteria keep upstream's names and order.
2. **The redaction section** (`SKILL.md` → "Redact before you show anything").
   Also close to verbatim: `<REDACTED>` in place of the secret, loops built
   against environment variables so the credential stays in the environment,
   quoting only the lines that carry signal, and stopping to ask when the
   redacted output no longer supports a diagnosis.

3. **The trigger vocabulary** (`SKILL.md` frontmatter). Upstream fires on
   *"diagnose"/"debug this", or reports something broken/throwing/failing/slow*;
   ours keeps that set and adds zh-TW equivalents. Adapted, not invented.

A 2026-08-17 review found this file listing only the first and describing the
second under what it *added*, which is the one direction the distillation plan
says not to get wrong: calling a substantial portion a concept rewrite. A
re-fetch of the pinned upstream later the same day added the third. All are named
here, and the full licence below covers them.

**Rewritten concepts.** The phase sequence, the feedback-loop constructions, the
ranked-and-falsifiable hypothesis rule, one-variable probing, tagged temporary
instrumentation, measure-before-fix for performance, "no correct seam is itself
the finding", and the cleanup gate are upstream's ideas in this repo's words.

**Dropped.**

- The human-in-the-loop rung (`scripts/hitl-loop.template.sh`). Nothing in this
  repo's verification surface needs a human to click, and a rung pointing at an
  absent script is worse than no rung.
- The opening instruction to read `CONTEXT.md` and consult ADRs. This repo does
  not have those and the plan forbids creating them; `AGENTS.md` and
  `docs/architecture.md` already own that role.
- **"Tighten the loop"** — upstream's instruction to treat the loop as a product
  and keep improving it: faster, sharper signal, more deterministic. Found missing
  by the 2026-08-17 re-fetch. This skill's gate requires a loop that is *already*
  fast and deterministic; it never asks anyone to make an existing one better, and
  that is a real omission rather than a decision. Left out for now rather than
  added late without a place earned for it, and recorded in
  `docs/research/upstream-distillation-ledger.md` with its cost.

**Added, with no upstream counterpart.**

- An explicit authority split. Upstream's Phase 5 walks from diagnosis into a
  regression test and a fix with no gate between them; here diagnosis and repair
  are separate authorities and ambiguous means diagnosis.
- *A seam must reach the observable result, not only the action you control.*
  Upstream's tautological category does not cover this shape — the assertion can
  be entirely true and still unrelated to the outcome. It comes from a local
  2026-08-17 incident, not from upstream.
- *Absence after a change is not evidence when the symptom was never produced on
  demand.* Upstream implies it by gating on a red-capable command; stating it as
  its own rule is local, and it is there because that is the move a local
  incident actually made.

## Rechecking

`scripts/upstream-recheck.sh` re-fetches the pinned files and checks them
against the hashes the ledger was written against; the per-section disposition is
in `docs/research/upstream-distillation-ledger.md`. Start there.

Resolve the current marketplace pin before comparing — do not assume this SHA is
still what the marketplace serves. Compare only `diagnosing-bugs`. Classify each
upstream change as adopt / adapt / already-covered / reject, reopen
`references/tuning.md` before deciding, and advance the SHA above only after the
selected diff has been reviewed. A pin that moved is not by itself a reason to
follow it.

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
