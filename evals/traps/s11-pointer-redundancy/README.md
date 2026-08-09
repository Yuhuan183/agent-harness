# s11-pointer-redundancy trap

Three resident contract clauses name a skill and then restate that skill's own
`description` almost word for word, with both copies resident every session.
This fixture asks whether the contract copy does anything.

Not a word-count exercise. The whole resident layer is 0.93% of a p50 prompt and
these clauses are a rounding error inside it. What is at stake is whether the
**contract layer** carries force a **catalogue entry** does not — the assumption
six role files, three skills and the slimming spec are organised around, and the
one direction 1 weakened by establishing that the contract arrives as user
context with probabilistic compliance. Two rules we treat as authoritative give
opposite answers, and only one of them can govern future compression:

| rule | verdict on these clauses |
|---|---|
| one policy, one place, said once (OpenAI) | the contract copy is redundant |
| authority in the contract, procedure in the skill (this repo) | the contract copy declares an obligation |

## Layout

| Path | Role | Show to agent under test? |
|---|---|---|
| `scenarios/` | six verbatim opening messages, one per cell | that scenario only |
| `GROUND-TRUTH.md` | design, reach markers, decision rule, construct limits | never |
| `arms.py` | builds the arm-B contract text; pure, writes nothing | never |
| `run.py` | swaps the deployed contract for arm B and puts it back | never |
| `grade.py` | mechanical answer sheet (reads the event stream, not the agent's account) | never |
| `surface.tsv` | the bytes a result row depends on | — |

## Protocol

Arm A is the machine as it already is. Arm B removes one clause from
`~/.claude/CLAUDE.md`, because that file is the surface under test and no flag
can vary it — an isolated `HOME` loses the credentials (probed 2026-08-08:
"Not logged in").

```bash
./run.py --clause headroom-protocol --arm b --dry-run          # writes nothing
./run.py --clause headroom-protocol --arm b --preflight \
         --scenario scenarios/h1-large-blob.md --out runs/h1-b-1.jsonl
./grade.py --events runs/h1-b-1.jsonl --scenario scenarios/h1-large-blob.md
```

`--preflight` is the manipulation check: it asks the model whether the contract
contains the instruction and compares the answer to the arm. Arm B whose clause
never left the context is not a data point, and this is the only way to know.

Grader exit codes are three-valued on purpose: `0` correct, `1` incorrect, `2`
**invalid** — the run never reached the branch under test. Invalid runs are
recorded and counted, never dropped; their rate says the scenario is broken
rather than the harness.

### Restoring, if a run is interrupted

`run.py` restores in a `finally` and verifies by hash, and refuses to start when
`~/.claude/.s11-arm-b-in-progress` exists or the deployed contract already
differs from the repo source. If it ever reports `RESTORE FAILED`, the snapshot
path is printed; `scripts/sync.sh --apply` also redeploys from source. Note that
`sync.sh` runs the suite first and will refuse while anything is red — during
the build of this fixture that behaved exactly as intended and blocked a deploy,
which is worth knowing before assuming it is broken.

## Negative controls

Three of the six cells (`h2`, `p2`, `b2`) pass only when the skill is **not**
loaded. Every other trap in this repo asks whether a rule fires and none asks
whether it over-fires; on 2026-08-08 a do-nothing agent was shown to pass both
s7 and s8 for exactly that reason. A fixture that only rewarded loading would
breed an agent that loads everything.

## Before reading any result

- The three clauses are **not equally separable**. Only `headroom-protocol` is a
  clean present/absent contrast; for the other two the skill's name survives
  elsewhere in the contract, so arm B tests the narrower "does the explicit
  instruction carry it, given the name is there anyway". Every row says which.
- Opportunities are **constructed**, because natural triggers ran at four
  occurrences across 86 transcripts. A built scenario makes the trigger more
  obvious than real work does.
- A passing arm B is **weak** and authorises nothing. Only a failing arm B is
  strong, and it would argue against deletion, not for it.

## Results log

> **A first batch of 20 runs on 2026-08-08 is archived under `runs/unprovenanced/`
> and does not count.** Its driver piped `run.py`'s stderr to `/dev/null`, so no
> artifact recorded which contract each run executed under — the post-run diff
> proved the file was restored, never what it was during the call. Every arm-B
> row was therefore a claim about a condition nothing could confirm, which is
> the failure the surface fingerprints exist to prevent, one level down. The
> runs below record the contract sha and the remaining name count per run.

**2026-08-08, `provider-routing`, `[surface 32cc98cf]`, Claude Code 2.1.226.**
30 runs, 3 arms × 2 cells × 5 seeds. Zero invalid, zero run failures.

> The stamp stays at `32cc98cf` because that is what produced these rows. An
> audit immediately afterwards fixed a leak in `run.py` — the MCP config was
> written with `delete=False` into the system temp dir — which moved the surface
> to `6ccd707a`. The rows are **not** re-stamped: back-dating a fingerprint onto
> bytes that did not produce it is the failure this mechanism exists to catch.
> What can be said instead is checkable — all 30 `.meta.json` files record
> `mcp_attached: false`, so the changed code path was never on this batch.

| Arm | Contract | Mentions left | p1 (should load) | p2 (should not load) |
|---|---|---|---|---|
| A shipped | `12a0d188f9ea` | 2 | **5/5 loaded** | 5/5 stayed away |
| B pointer removed | `35ba056f2de3` | 1 | **5/5 loaded** | 5/5 stayed away |
| C every mention removed | `7cb97309ebb8` | 0 | **5/5 loaded** | 5/5 stayed away |

Manipulation check, 13 observations: arm A answered YES 3/4, arms B and C
answered NO 7/7. One arm-A run said NO while the clause was present, so the
control is noisy in the direction of under-reporting. What it establishes is the
part that matters: arm A **can** report the clause, which it could not do if the
contract never reached the session — the alternative explanation that would have
made this whole null meaningless.

**Reading, against the rule declared before the runs.** Arm A 5/5 and arm B 5/5
is not a separation, so this records as **no separation at n=5**, not as "no
difference". A passing arm B authorises nothing. What is new is arm C: with the
skill's name absent from the contract entirely, loading was unchanged, so on
this cell the contract contributed nothing measurable and the description
carried the routing alone.

Four limits, none of them footnotes:

- **Arm C was designed after seeing arm B**, so its decision rule was inherited
  rather than pre-registered. It cannot be read as a confirmed prediction. The
  outcome is a null, which is the direction post-hoc design cannot manufacture,
  but the asymmetry is worth stating.
- **Arm C is not a pure name removal.** Erasing the second mention meant
  deleting the verifier clause's trigger condition, so arm C also relaxes when
  an outcome verifier is allowed (`arms.py` records this as its side effect).
- **Ceiling effect, measured rather than assumed.** The p1 prompt and the skill
  description share `GPT`, `fallback` and `profile`. That is an explicit trigger
  — not the near-verbatim overlap an earlier note claimed, but explicit enough
  that both arms sit at the ceiling and a difference would have to be large to
  show. An oblique-trigger variant is the obvious next cell.
- **One headless turn, fresh session.** No compaction, no long context, no
  mid-session moment where a skill is most likely to be forgotten — plausibly
  where a contract clause earns its keep, and exactly where this cannot look.

The negative control is what makes the rest readable: p2 stayed away 15/15
across all three arms, so the 5/5 on p1 is not an agent loading everything.

### p3 oblique trigger — 15 runs, all **invalid**, scenario defect

Added to attack the ceiling: p1 hands the agent `GPT`, `fallback` and `profile`,
which the description already contains, so a difference between arms would have
to be large to show. p3 was worded to share zero tokens with the description
(measured, not assumed) while describing the same situation.

It does not describe the same situation. All 15 runs loaded nothing, which at
first read looked like a clean floor — the contract failing to rescue an oblique
trigger — and that reading is wrong. Reading the transcripts:

| what the runs actually did | count |
|---|---|
| read "換另一邊的工具" as a worktree / agent handoff, not a model provider | 15/15 |
| concluded the handoff was impossible and stopped | 14/15 |

The fixture is a bare directory holding one six-line stub and is not a git repo,
so the agent correctly reasoned that there was nothing to hand off and no
mechanism to hand it off with. The routing branch was never reached.

The grader scored them `incorrect` rather than `invalid` because the marker
included `settle_batch`, which any run that opens the file produces. That is the
same marker-design failure the dry run was supposed to have fixed: a token that a
derailed run can still emit. **All 15 rows are reclassified invalid and excluded
from every count above.** They are kept, because an invalid rate is data about
the scenario, and this one says the scenario was broken in three ways at once —
ambiguous wording, a fixture that cannot support the task, and a marker that let
both through.

### p3 rebuilt — `p3-capability-choice`, 15 runs, `[surface 7af69201]`

All three defects fixed and each verified separately. The wording asks whether
the agent should do the work itself or hand it to a stronger model, which cannot
be read as a worktree handoff and still shares **zero** tokens with the
description (measured). The fixture is a real git repository with a 38-line
multi-currency ledger and four passing tests, so the task is possible and worth
discussing. The marker accepts only an answer to *who does the work*, and was
checked against a simulated run that reads the file and answers nothing — which
now scores invalid, the exact case that slipped through before.

| Arm | Mentions left | Loaded the skill |
|---|---|---|
| A shipped | 2 | **0/5** |
| B pointer removed | 1 | **0/5** |
| C every mention removed | 0 | **0/5** |

Zero invalid this time, and the transcripts say why that is trustworthy: 15/15
engaged with the capability question, 0/15 claimed the task was impossible, and
each run made 6–10 tool calls investigating the module first. The replies are
substantive routing answers — one weighs dispatch overhead against the module's
size, notes that no stronger tier exists above the current one, and concludes the
real blocker is an accounting question only the user can settle.

**So the ceiling is gone and the finding holds at both ends.** With an explicit
trigger every arm loads; with a trigger that needs a semantic hop no arm loads.
The contract's mentions changed nothing either way. What decides loading here is
how closely the request's wording sits to the description's, which is a property
of the description and not of the contract.

That has a measurable cost, which is the more useful half of this result: **5 of
the 15 replies named `GPT-5.4`, while the model this repo actually routes to is
`gpt-5.6`.** The skill that did not load is where that fact lives. The lever this
points at is therefore the description's coverage of oblique phrasing, not the
contract clause — deleting or keeping the clause would not have moved any of
these 45 runs.
