# Attribution — the `INTENT:` / `TWINS:` / `AUTH:` gate lines

Derived from Sahir619's Fable Method.

- **Source**: <https://github.com/Sahir619/fable-method>
- **Upstream files**: `skills/fable-method/SKILL.md` (the three gate lines, the
  authority order, the documentation-is-not-authorization rule, the artifact
  gate) and `skills/fable-judge/SKILL.md` (the fraud list).
- **Reviewed release**: plugin `v1.4.0`
- **Reviewed commit**: `88b5cf36b10ee3679e08ee0f0181b9774d481508` (2026-07-15),
  which is also the current head — upstream has not moved since, checked
  2026-08-28. The distillation happened on 2026-07-22, so this commit is what
  was read even though the pin was recorded six weeks late.
- **Licence**: MIT, Copyright (c) 2026 Sahir619. Full text below.

## Why this file exists later than the borrowing, and where it lives

It did not exist until 2026-08-28. The borrowing landed 2026-07-22; for five
weeks the three gate lines shipped in six deployed role files with no notice
attached, and no check could see it: `test_every_attribution_pins_a_commit_and_carries_its_licence` (then named `test_every_derived_skill_pins_a_commit_and_carries_its_licence`)
walked `main/.agents/skills/*/ATTRIBUTION.md`, and `scripts/upstream-pin-report.py`
derives its list from those same files. Both read what had been written down.
This had not been, so the repo's own answer to "which upstreams do we distil
from" was four, and the correct answer was five.

It lives here rather than beside the roles because `main/claude/agents/` is an
agent-registration directory — `test_roles.py` globs `*.md` there and compares
stems against the role list, and the client reads it the same way, so a notice
dropped in would be parsed as a broken role. `main/.agents/scripts` deploys to
`~/.agents/scripts` under an existing manifest row and holds `gate_lines.py`,
the single source of the regexes that match these lines. The notice therefore
travels with the artifact it covers.

## What was taken, and how

**Substantial portions — three format lines, near-verbatim.** Ours are
shortened forms of upstream's, not independent constructions:

| | Upstream (`fable-method/SKILL.md`) | Ours |
|---|---|---|
| Intent | `INTENT: code does <X>; the failing check/task expects <Y>; the spec (README/docs/docstring) says <Z>` | `INTENT: code does <X>; the check/task expects <Y>; the spec says <Z>` |
| Twins | `TWINS: searched <the pattern> - found <N> other sites: <files, or "none">` | `TWINS: searched <pattern> - found <N> other sites: <files or "none">` |
| Auth | `AUTH: user said "<their exact words>"` | `AUTH: user said "<words>"` |

A 2026-07-22 note in `docs/research/trap-experiments.md` recorded upstream's
intent line without its articles, which made ours look like an expansion of
upstream's rather than a contraction. The table above is written against the
fetched bytes.

These ship in `main/claude/agents/{executor,mech-executor,security-executor}.md`
and the three `main/codex/agents/*.toml` twins, all deployed.

**Also substantial, in substance rather than wording.**

1. **The authority order.** Upstream: an explicit user statement beats the spec,
   the spec beats the tests, the tests beat current code behaviour, and a
   framing like "make the tests pass" does not promote the tests above the spec.
2. **Documentation is not authorization.** Upstream states it as its own rule —
   a README or workflow doc saying a deploy "must follow" your change makes the
   action documented, never authorized. Ours narrows to repository docs.
3. **The artifact gate.** Upstream sweeps the finished report for owed lines and
   repairs mechanically, firing only when something is owed and missing. Ours is
   `qc-gate-lines` plus `gate_lines.py`; the mechanism is a script rather than a
   final self-check, the rule is upstream's.
4. **The QC fraud list** (`fable-judge/SKILL.md`): weakened checks, fabricated
   fixtures, out-of-scope changes, leftover debris.

**Rewritten concepts.** The trap-fixture approach to behavioural evaluation, and
the "a rule with no failing trap is a deletion candidate" covenant.

**Dropped.**

- **The `PENDING:` line** — a prescribed-but-untaken follow-up declared verbatim.
  Not adopted, and not previously recorded as a decision.
- **The recall gate**, the seven-step loop as a resident contract, the domain
  adapters, and `fable-judge` as a second gate. The last was refused on this
  repo's never-stack-gates rule.

**Added, with no upstream counterpart, and every one of them from local
evidence.** Upstream mandates the lines; these say how they fail here:

- *Emit them as plain text at the line's first character, no bold or other
  markdown wrapping.* From `s7o7`, where the lines were wrapped in markdown
  emphasis and became unmatchable.
- *In English even when the rest of the report is in another language.* From
  `gs1`/`gs2`/`gs3`, where the GPT-5.6 bridge kept the substance and paraphrased
  the template into Chinese.
- *Fill `<Z>` with the spec's stated rule in the spec's own words, never just an
  example value.* From `s7o4`/`s7o5`.
- *`TWINS:` is report-only; fix extra sites only when already in approved scope.*
  Upstream says "fix them or list them"; the narrowing is this repo's authority
  split.
- *The `AUTH:` quote permits, it never overrides sandbox or scope limits.*

## Rechecking

Upstream is one plugin with four skills. Re-fetch rather than re-reading this
file, and compare the two files named above; hashes at the pinned commit:

| Upstream file | sha256 (first 16) | bytes |
|---|---|---|
| `skills/fable-method/SKILL.md` | `b3d1592a6096ffad` | 17797 |
| `skills/fable-judge/SKILL.md` | `c363ca6842982292` | 6098 |

Re-classify every section, not only the ones listed here: the entries that exist
are the ones somebody already thought about, and this attribution's own
five-week absence is what that failure looks like at the file level.
`scripts/upstream-pin-report.py` covers this upstream from the day this file
lands, because it derives its list from these files.

## MIT Licence

MIT License

Copyright (c) 2026 Sahir619

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
