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

**Not classified.** The seven role files under `main/claude/agents/` were not
re-traced against `templates/agents/*.md` at this pin. `docs/research/peer-harnesses.md`
records that the role set converged independently (ours predates the
adoption), but that is a coverage statement, not a wording pass.

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
