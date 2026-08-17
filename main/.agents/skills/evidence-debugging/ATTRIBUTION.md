# Attribution — evidence-debugging

Derived from Matt Pocock's agent skills.

- **Source**: <https://github.com/mattpocock/skills>
- **Upstream skill**: `skills/engineering/diagnosing-bugs/SKILL.md`
- **Reviewed release**: `v1.2.3` (2026-08-06)
- **Reviewed commit**: `068b6e0c62393147daf03530149cdce209c93da8` — the Claude
  marketplace pin resolved on 2026-08-17, not the release tag. The two disagree
  by twelve commits while the version string does not move, so the SHA is the
  only thing that identifies what was read.
- **Licence**: MIT, Copyright (c) 2026 Matt Pocock. Full text below.

## What was taken, and how

**Substantial portion — the Phase 1 completion criterion.** `SKILL.md`'s "The
gate" section is a close adaptation of upstream's, and deliberately so: its value
is in the precision of the wording — *already run at least once*, *red-capable*,
*asserts the user's exact symptom*, and the instruction to stop when a theory
arrives before the command does. Paraphrasing weakens it. This is why the full
licence sits below rather than a bare notice.

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

**Added, with no upstream counterpart.**

- An explicit authority split. Upstream's Phase 5 walks from diagnosis into a
  regression test and a fix with no gate between them; here diagnosis and repair
  are separate authorities and ambiguous means diagnosis.
- *A seam must reach the observable result, not only the action you control.*
  Upstream's tautological category does not cover this shape — the assertion can
  be entirely true and still unrelated to the outcome. It comes from a local
  2026-08-17 incident, not from upstream.
- The redaction section is upstream's; the instruction to stop and ask when the
  redacted output no longer supports a diagnosis is kept verbatim in effect
  because it is the part that prevents quiet over-sharing.

## Rechecking

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
