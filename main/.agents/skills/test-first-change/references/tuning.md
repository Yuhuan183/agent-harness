# test-first-change — agent-harness tuning

Owned by this repo. `SKILL.md` holds what is true of test-first work anywhere;
this holds what is true *here*, including every worked example — upstream's are
TypeScript and Jest, and this repo has neither. Upstream rechecks may change
`SKILL.md`; they may not change this file.

This layer does not outrank a system or developer instruction, the current
request, or the global contract. It records defaults this project has found hold
repeatedly, and stop conditions it has paid for.

## Authority

- Being model-invoked is not authority to mutate. A named seam is not either.
- The verbs that grant a behaviour change: implement, add, change, extend, fix,
  修掉, 加上, 改掉, 實作. The verbs that do not: review, explain, assess, plan,
  評估, 看一下, 說明. Ambiguous means propose the check and wait.
- Commit, push, publish, opening an issue and deploying each need their own
  explicit authority, and permission to change behaviour implies none of them.
- Never dispatch a subagent from inside this skill. Hand it back to the
  session's dispatch skill and let the existing payoff test decide.
- An unexplained defect is [evidence-debugging](../../evidence-debugging/SKILL.md)'s
  work, not this skill's. Come back once the cause is known.
- Refactoring is not part of the red-green loop. Tidying inside the change is
  fine; touching code outside the approved slice is a separate scope with its own
  reason, even when the checks stay green.

## This repo's three verification surfaces

| Surface | Where | What it can observe |
|---|---|---|
| Python `unittest` | `main/claude/tests/` | source text, generated artifacts, subprocess output, budgets |
| shell checks | `evals/replay/fixtures/*/check.sh` | a delivered artifact's exit status against real files |
| markdown contract assertions | `test_contracts.py`, `test_ledger.py` | resident prose, budgets, cross-surface agreement |

They share one property worth stating: none of them is a mock. Every one reads
the bytes that ship. A change that needs a fourth surface is a decision to
raise, not a file to add.

## Worked pairs

Each bad half is a real shape this repo has shipped, not an invention.

**Python — an assertion guaranteed by construction.**

```python
# bad: the function's only job is to export that variable, so this can never
# disagree with the source. It was green while the setting stayed on.
self.assertIn("HEADROOM_LOSSLESS=1", read("install-zsh-functions.sh"))

# good: assert the state the launcher was supposed to reach, at the surface
# that actually decides it.
self.assertEqual(False, settings_the_proxy_reads()["ccr"]["tool_injection"])
```

**Shell — a check keyed on the artifact's shape.**

```sh
# bad: exits 0 for an empty report, a truncated report, and a wrong one.
[ -f "$1" ]

# good: recompute the claim from the input and compare.
[ "$(jq '[.rows[].amount] | add' "$1")" = "$(expected_total)" ]
```

**Markdown contract — an assertion that reads the heading, not the content.**

```python
# bad: passes as soon as the section exists, whatever it says.
self.assertIn("## Verification", doc)

# good: every command the doc names has to resolve here.
for command in commands_in(doc):
    self.assertTrue((ROOT / command.split()[0]).exists(), command)
```

## Ratchets, the local idiom

Budgets and counts in this repo are measured then frozen: `metadata_budgets`,
per-document body budgets, the unstamped-row ceiling. Two rules come with them.

- Set the number from what you **measured**, not what you forecast. A ceiling
  granted for a body not yet written is a budget issued on an estimate.
- Raising one is a decision with a reason written beside it. Raising one to make
  a change fit is the change asking to be smaller.

## Verification, in this repo's terms

- The narrowest check that could actually refute the claim, not the broadest
  suite available.
- **A seam must reach the observable result, not only the action you control.**
  When a check establishes "the request was sent" but not "the effect happened",
  write the second down as uncovered. Local rule, from a 2026-08-17 incident
  where a passing test asserted a launcher exported a variable while the setting
  it was meant to change stayed on, recorded in `docs/research/landing-log.md`.
  Named, not linked — this file is deployed outside the repo, where no relative
  path reaches that tree.
- A green test that bypasses the real failing path — the actual parser, file
  system, shell, provider or proxy — cannot close the claim. Say which path
  stayed unexercised.
- Non-deterministic behaviour needs a measured rate quoted before and after, not
  "seems better".
- Every reach-marker mistake in `evals/replay/` was caught by running the gate,
  never by reading the grader. Run it.

## Reporting

Traditional Chinese (Taiwan) to the user; English for code, identifiers,
commands and any instruction another agent will read.

Lead with the outcome. Then, and only what applies:

- the check, its observed failure, and its pass — in that order;
- the seam chosen and what it does not reach;
- the change, kept to what the check demanded;
- what remains uncovered, and the check that would cover it.

Mark a choice the request did not specify as `DECISION: <what and why>`. Mark
uncertainty only where it could change the conclusion.

## Known asymmetry, first release

`agents/openai.yaml` sets `allow_implicit_invocation: false`, so Codex requires
an explicit `$test-first-change`. Claude has no equivalent switch — it decides
from the `description`, so implicit invocation stays live there. The two
providers therefore differ in how this skill starts, deliberately and only until
description discrimination has been measured. Do not describe the first release
as explicit-only without naming which provider.
