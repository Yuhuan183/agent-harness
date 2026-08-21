# Attribution — baton-dispatch

Derived from CabLate's Baton.

- **Source**: <https://github.com/cablate/baton>
- **Upstream file**: `SKILL.md`, the whole of it — Baton is one file plus a
  README, so there is no index-versus-content split to get wrong here.
- **Reviewed release**: `v0.1.1` (2026-07-10)
- **Reviewed commit**:
  `0ab4d2ec5c69820001eeac2a12fab2c87fd3e943` (2026-07-16, "Prevent delegated
  scope expansion") — **after** the release tag, and the reason the tag alone is
  not the pin. That commit added a whole section, and anyone distilling from
  `v0.1.1` would have shipped without it. Upstream has not moved since.
- **Licence**: MIT, Copyright (c) 2026 CabLate. Full text below.

Upstream's text is not vendored here. The skill body names the source in one
sentence; the resolvable pin lives in this file and in
`docs/research/peer-harnesses.md`, because a bare short SHA in a deployed file
cannot be resolved by whoever reads it (`docs/README.md` rule 9). A recheck must
fetch upstream; re-reading this file is not a recheck.

## Why this file exists later than the skill

It did not exist until 2026-08-21, and the four other distilled skills had one
from the start. The cost was paid the same day: a survey of this upstream began
by looking for an ATTRIBUTION file and for the repository in `docs/`, found
neither, and concluded the skill had no upstream — the source was sitting in one
sentence of the skill body the whole time, and the user had to point at the
repository. The classification below is written against the fetched `SKILL.md`,
not from memory of it.

## What was taken, and how

Upstream is 102 lines of decision rules across seven sections. This skill is
larger because it also carries route mechanics, ledger records and QC, which
Baton does not have.

**Substantial portions.** These are upstream's ideas, kept close to upstream's
shape:

1. **The dispatch brake.** Delegation is not free and must clear its own
   overhead before it happens. Upstream opens with it; this skill's "Cost test"
   is the same rule with local numbers (a high-tier pinned agent costing about
   as much as main) and four named payoffs.
2. **The invariants.** Final judgment stays with the main agent; no
   parallelising unresolved shared contracts or overlapping writes; minimum
   sufficient context, exact scope, output shape and stop condition per worker;
   centralised expensive verification; verified facts separated from reasoned
   conclusions; failed, partial and skipped work treated as coverage gaps.
3. **The approved release scope** (commit `0ab4d2ec`). The plan or approved
   slice as a hard dispatch boundary, workers reporting adjacent opportunities
   without implementing them, and the pause list — new domain, table, API
   surface, external service, deployment responsibility. In "Run design".
4. **Global stop conditions.** Objective satisfied, budget reached, no material
   progress, same-cause repetition, invalid ownership boundaries, cost exceeding
   remaining benefit. Distributed across this skill and
   `references/briefs-and-stops.md` rather than kept as one list.
5. **Fall back to direct execution when delegation repeatedly fails**, and
   **slice completion is a checkpoint, not authority for the next phase**. Both
   adopted 2026-08-21, both previously absent. The first is merged with
   `miyago9267/pilotfish-codex` 1.6.1's circuit breaker, which reaches the same
   place from the other side and adds the sharper half — losing the review
   service is not a user decision.

**Rewritten concepts.** Choosing an execution primitive, the standard workflow,
and "change the prompt, task boundary, primitive, or verification strategy after
repeated same-cause failure" are upstream's ideas in this repo's words and
units.

**Written locally, with no upstream counterpart.** Route resolution and provider
selection (upstream is provider-neutral), the fixed `[LEAF_DISPATCH]` /
`[LEAF_RESULT]` record formats, the experience ledger, QC tiers and the
false-completion fraud list, the five-pass verification cap, the two-revision
Plan convergence rule, the readiness-unit ID, and the Claude/Codex twin split
including the no-Bash rule for read-only roles.

**Dropped.** Upstream's capability adapters and its "Keep the skill current"
section: this repo keeps that discipline in `docs/` and in the test suite rather
than inside a skill body, and adapters would duplicate `provider-routing`.

**Clause by clause (2026-08-21).** The coverage pass asked whether each upstream
rule had a local equivalent. This asks the different question the licence cares
about: how close is the wording. Five clauses are close enough that the credit
has to be explicit rather than folded into "these are upstream's ideas".

| Upstream | Ours | Reading |
|---|---|---|
| "Treat the current plan or owner-approved release slice as a hard dispatch boundary" | "The approved Plan or release slice is a hard boundary" | Near-verbatim; only the verb and the article differ |
| "Treat completion of the current vertical slice as a checkpoint; do not automatically dispatch the next phase" | "Finishing a slice is a checkpoint, not authority to dispatch the next phase" | Same sentence, compressed |
| "Pause before adding a new domain, data table, API surface, external service, or deployment responsibility" | "stop before adding a domain, table, API, service, deployment responsibility" | **The list itself is upstream's**, item for item and in order |
| "Define the outcome, non-goals, constraints, and evidence required" | "Stabilize outcome, scope/non-scope, constraints, evidence…" | The same four items in the same order, with two local additions |
| "Converge shared contracts, schemas, registries, and architecture decisions before fan-out" | "Converge shared schemas, registries, config, generated output, and lockfiles" | The rule and two list items are upstream's; the rest is local |

Everything else measured below a quarter overlap on content words and reads as
this repo's own sentences carrying upstream's idea — "keep final judgment with
the main agent" and "centralize expensive verification" are the two closest of
those, and both were rewritten around local units rather than adapted.

The classification direction that matters is calling a substantial portion a
concept rewrite, so the five above are listed even where the compression is
heavy. The MIT text was already reproduced in full below, so this pass changes
the precision of the credit and not the licence position.

## Rechecking

Fetch <https://raw.githubusercontent.com/cablate/baton/main/SKILL.md> and
compare against the commit above; do not work from this file. Releases are not
the unit — the pin is a commit after `v0.1.1` precisely because the release
missed a section. Classify every upstream rule as adopt / adapt /
already-covered / reject, and record the disposition in
`docs/research/peer-harnesses.md`; a rule left unclassified is the one that goes
missing. Advance the commit above only after the selected diff has been
reviewed. A pin that moved is not by itself a reason to follow it.

## MIT Licence

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
