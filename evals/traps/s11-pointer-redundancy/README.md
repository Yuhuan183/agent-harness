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

> No runs yet. The harness landed 2026-08-08 with arm A unrun; the first rows
> must carry `[surface <short>]` from `evals/scripts/trap-surface.py`.

| Date | Clause | Arm | Scenario | Preflight | Verdict | Surface | Notes |
|---|---|---|---|---|---|---|---|
