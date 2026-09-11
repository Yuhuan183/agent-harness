# Attribution — provider-routing

Derived in part from Nanako0129's Pilotfish. Most of this skill is this
repository's own work; the part that is not is named clause by clause below.

- **Source**: <https://github.com/Nanako0129/pilotfish>
- **Upstream file**: `templates/claude-md.orchestration.md`, the resident
  orchestration policy (58 lines at the pin), which is where the verifier
  placement rules live.
- **Reviewed release**: `v1.3.10` (2026-08-08)
- **Reviewed commit**: `7a7f71b327f079fecbf29fa91e444b9a6180c31c` (2026-08-08,
  the tag commit). The borrowing happened on 2026-07-22 against an earlier
  v1.3 release; this is the commit whose text the clause table was checked
  against, and the pin `docs/research/peer-harnesses.md` already carries.
- **Licence**: MIT, Copyright (c) 2026 Nanako0129. Full text below.

## Why this file exists seven weeks after the borrowing

Pilotfish was filed as a *peer* (同業) in the research tier from the start,
with a full pin and a rule-by-rule comparison table, and every one of those
rows says 已落地 - already true here. What nobody asked until the 2026-09-10
re-trace was the licence's question rather than the coverage question: not
"do we have this rule" but "how close is the sentence". Three sentences turned
out to be Pilotfish's, compressed. A peer whose sentences ship in a deployed
skill is an upstream, whatever the research tier called it.

## Clause by clause

| Upstream (at the pin) | Ours | Reading |
|---|---|---|
| "Risk-triggered completed work gets one fresh outcome-verifier pass at smallest coherent integration boundary where full claim can be refuted." | "Place the verifier at the smallest coherent integration boundary where the complete acceptance claim can be independently refuted." (`references/verifier-triggers.md`) | Near-verbatim; "independently" is local |
| "Verify earlier at security, cross-language/FFI, serialization/pre-aggregation, irreversible, or integration-blocking boundaries." | "Verify earlier for security, cross-language or FFI, serialization or pre-aggregation, irreversible-operation, and integration-blocking boundaries" (same file) | **The list is upstream's**, item for item and in order |
| "Named-role model routing lives in agent definitions. Omit invocation `model`; override would replace role routing." | "Named Claude roles own model and effort in frontmatter; omit invocation-level `model` except to sample a second rung deliberately." (`SKILL.md`) | Same rule, same shape; the exception clause is local |

**Rewritten concepts.** One outcome verifier per top-level task (upstream:
"one fresh outcome-verifier pass", "avoid micro-verifier calls"); the
security review-then-execute split with one writer (upstream's
`security-reviewer` -> `security-executor` sequencing, whose near-verbatim
sentence lives in `baton-dispatch` and is credited there).

**Written locally, with no upstream counterpart.** The trigger list itself
(upstream's is "security/trust; destructive/irreversible/external mutation;
data/schema/serialization/migration; release; material cross-component
acceptance" - ours shares three items and adds money, concurrency, public
APIs, cross-repo compatibility, adversarial acceptance, conflicting evidence
and failed reproduction, and drops release); CP-first provider choice; the
H/X profiles; the Codex bridge resolution procedure; single-hop cross-provider
fallback; the independence rule for which provider verifies; the provider
extension protocol; route evidence and the ledger tie-in. Upstream is
single-provider and has no provider fallback or cost ranking at all.

## The role files, traced 2026-09-10

The line that stood here said the seven role files under `main/claude/agents/`
had not been re-traced against `templates/agents/*.md`. They have been now,
against four upstream versions rather than one, because the question is which
text came first and a single pin cannot answer it.

**Most of it is rewritten, and that is measured rather than asserted.** Pairing
each role body against its upstream counterpart at `v1.2.1` and counting shared
six-word sequences of content words gives 0 or 1 per pair; the longest common
run is four to six words and every one of them is generic (`glob/grep first
read only relevant excerpts`, `you are read-only leaf`). The sentences are this
repo's own. What matches is the *order of the items inside them*, which is
what a concept rewrite looks like.

Three things are not rewritten, and two of them are owed to upstream:

| Upstream | Ours | Reading |
|---|---|---|
| `v1.3.4` (2026-07-25) `plan-verifier.md`: the `Blocker:` / `Evidence:` / `Minimum revision:` / `Acceptance check:` block, placeholders included | the same block, verbatim, in `main/claude/agents/plan-verifier.md`, `main/codex/agents/plan-verifier.toml`, and quoted by both dispatch skills | **Substantial portion.** Ours landed 2026-07-28 in a commit titled "adopt pilotfish v1.3.4 controls", so the borrowing was declared in history and never in a notice |
| `v1.2.1` (2026-07-16) `security-executor.md` description: "pre-approval analysis belongs to security-reviewer" | the same sentence, verbatim, in our `security-executor` description | **Substantial portion, and it sits on the resident surface** - a description is loaded every session, so this one is read more often than any other borrowed text here |
| `v1.2.1` long-work clause: "the exact command, its absolute working directory (including the isolated worktree path), and every required environment variable or input path" | "its exact command, absolute working directory, required environment, and inputs" in four role bodies | **The list is upstream's**, item for item and in order; the sentence around it is ours |

**One finding runs the other way.** The third verdict is ours. `INCONCLUSIVE`
entered our `verifier` on 2026-07-22; upstream shipped `CONFIRMED` or
`REFUTED` only through `v1.3.4` (2026-07-25) and added the third in `v1.3.5`
on 2026-07-29, a week after us. `docs/research/README.md` lists "verdict 三分
(v1.3.5)" as 已落地, which reads as though we adopted it; the dates say we did
not.

**What this does not settle.** Upstream's seven-role split and the phrases
above existed at `v1.2.1`, four days before this repository's first commit.
That is priority in time, not evidence of copying, and no record of reading
Pilotfish before 2026-07-22 exists in this tree. The claim in
`docs/research/peer-harnesses.md` that the role set converged independently
therefore now rests on the absence of a record rather than on chronology, and
it is written down there in those terms.

## 2026-09-11: upstream has not moved since the 2026-09-10 check, and one 佐證

Head is still `ea0d20bb` (2026-08-28), so nothing here was re-classified. The
pin report called it `MOVED +19` because that count is measured from the
distillation pin rather than from the last look; the report now says so itself.

One commit in that already-seen range is worth recording. `#63` (`v1.4.1`)
removed upstream's blanket refusal of a symlinked `CLAUDE.md` and now accepts
one whose resolved target is a readable regular file. This repository's
`project-init` went the other way on the same day and **refuses** two manifest
targets that resolve to one inode. Both are right, because the shapes differ:
upstream writes one policy block into the user's global file, and a link is
then just a link; we render two blocks for two clients, so one inode means the
second render replaces the first and only one client's wording survives.

The 佐證 is not the disposition, it is the prevalence: an independent
implementation shipped a release for this, and three of the five
contract-bearing repositories in this workspace keep `CLAUDE.md` as a symlink.
Upstream also records what it did not fix - the pathname predicates and the
`grep` after them are not race-resistant, with descriptor-based validation
deferred - which is the kind of self-reported negative that raises trust in the
rest.

## Rechecking

Fetch
<https://raw.githubusercontent.com/Nanako0129/pilotfish/7a7f71b327f079fecbf29fa91e444b9a6180c31c/templates/claude-md.orchestration.md>
and compare against the three clauses above; re-reading this file is not a
recheck. From v1.4.0 upstream ships as a native plugin and the policy moved
to a SessionStart injection, so a recheck against a later pin has to find the
new carrier first. Advance the commit above only after the selected diff has
been reviewed and every rule re-classified; a pin that moved is not by itself
a reason to follow it.

## MIT Licence

MIT License

Copyright (c) 2026 Nanako0129

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
