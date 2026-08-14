# lifecycle replay

Three things this repo's controls are supposed to do had never been observed
doing it: surviving an interrupt, holding across successive corrections, and
handling leaf results that disagree. `docs/research/README.md` carried them as a
verification gap from 2026-07-28, and `docs/research/lifecycle-replay.md` set
four survival criteria a replay result must meet before it may be cited.

This directory closed criterion 2 — a scenario per question with its reach
marker written before anything ran — and then kept going. **92 runs retained,
2026-08-12 to 08-14**: 86 in batches, plus five pilots and one run the provider
aborted, all kept because an invalid run is data about the scenario.

Recount at any time with `ls -d runs/*/ | wc -l`; the figure above was typed by
hand as 82 first, which is the seventh instance of the failure Part 7 is about.

## What was learned, in one table

| question | answer | strength |
|---|---|---|
| does an interrupted session duplicate or drop work on resume? | no failure observed, 5/5 | exact 95% lower bound **0.478** — a true rate of one in two fits this data |
| do conflicting leaf results get quietly swallowed? | no, 5/5 surfaced both | same bound, same caveat |
| does a per-turn contract obligation survive successive corrections? | not reliably: 10 of 25 turns lapsed | and the lapse is **one request**, not decay |
| why does that one request never carry the marker? | unknown — 20 of 20 across four scenarios | three explanations built and killed |
| does the contract clause naming a skill change whether the skill loads, on the dispatch path? | no. three arms, 5/5 each | completes what s11's `b1` could not ask |
| can the resident contract beat a contradicting client instruction? | **yes, sometimes** — 3/5 with the confound controlled | refutes direction 1's blanket claim; rule-specific |
| do sessions reconcile the dispatches they make? | 15 of 33, swinging 4/5 to 1/5 on identical cells | the least stable thing measured here |

**Four hypotheses were built and refuted, three of them mine.** That is this
directory's main output, and Part 7 explains why it had to be.

---

## Part 1 — the construct

### Why this is not a trap

The traps in `evals/traps/` ask one question of one fresh turn, which is why
`s11/run.py` can pass `--permission-mode manual`: nothing it measures needs the
agent to write. Everything here is a property of a session that runs, is cut
off, is corrected, and dispatches — none survives being asked once with nothing
approved.

s11 proved that from the other side. Its `b1` positive cell could only ever
return zero, because the clause under test triggers on an **action** (`once a
dispatch is going ahead`) and the harness forbade every action. Three fixtures,
three reasoned refusals, and the fault was the harness rather than any fixture.
Reusing that runner would have inherited the fault verbatim.

### The harness, measured rather than assumed

Every row probed on 2026-08-12 against Claude Code 2.1.226, before a scenario
was written.

| need | setting | what the probe showed |
|---|---|---|
| more than one turn | `--session-id` then `--resume` | turn 2 answered `probe1.txt\|OK` with no tool available |
| the agent can act | `--permission-mode acceptEdits` | file written; under `manual`, nothing is |
| an interrupt lands mid-work | `SIGINT` at a wall clock | killed at 25 s with 9 of 12 files made, and it resumed |
| the resumed turn knows where it got to | `--resume` after `SIGINT` | answered `COUNT=9 LAST=9`, no tool available |
| leaves can be dispatched | default tools | two `Agent` calls, both returned |
| the workdir is writable | `mktemp -d` outside `~/.claude` | a write under `~/.claude` is refused outright |
| an injected client instruction arrives | `--append-system-prompt` | one session answered `CONTRACT=YES` and `INJECTED=YES`; delivery 10/10 |

### Two conditions with no control

- **The machine's hooks are live.** `--settings '{"hooks":{}}'` suppresses
  nothing — it loads *additional* settings, and a run launched with it still
  fired `SubagentStart`/`SubagentStop` into the real pending file. The only flag
  that silences user hooks, `--setting-sources project,local`, **also drops the
  user contract**: the same probe answered `CONTRACT=NO` where the control
  answered `CONTRACT=YES`. Contract and hooks arrive together or not at all.
- **So runs stage real dispatch stubs**, diverted rather than suppressed:
  `AGENT_EXPERIENCE_PENDING` and `AGENT_EXPERIENCE_LEDGER` point into the run's
  own directory. That keeps the machine's ledger clean and makes criterion 3
  recomputable per run, which a global ledger cannot do.

**This construct therefore measures the contract plus the hook layer.** The
traps measure the contract alone. Results do not transfer between them.

### Layout and commands

| path | role | show to agent under test? |
|---|---|---|
| `scenarios/` | the turns verbatim, plus pre-registered frontmatter | the turns only |
| `fixtures/build.py` | deterministic workdirs; every marker token generated here | the built files only |
| `run.py` | drives the session, interrupts it, swaps arms, retains everything | never |
| `arm.py` | contract swap with four guards and a hash-verified restore | never |
| `grade.py` | recomputes marker and outcome from artifacts | never |
| `summarise.py` | rebuilds the results table by regrading every run | never |
| `surface.tsv` | the bytes a result row depends on | — |

```bash
./run.py --scenario scenarios/r1-interrupted-resume.md --out runs/r1-001 --dry-run
./batch.sh r1-interrupted-resume 5            # resumable; skips completed seeds
./batch.sh d1-two-reviews 5 b                 # arm B: swaps the contract, restores it
./summarise.py                                # regrades everything, never reads verdict.json
./inject-probe.sh 10                          # delivery check for --append-system-prompt
```

### The rules everything here follows

- **A pilot is not a result.** At n=1 only `valid`/`invalid` may be cited.
- **A batch is 5 runs**, reported with an exact (Clopper-Pearson) interval. The
  lower bound is the finding; `100%` alone invites the opposite reading.
- **Marker before outcome.** A run that never reached the branch is `invalid`,
  neither pass nor failure — and invalid runs are counted, never dropped, since
  an invalid rate is data about the scenario design.
- **Criterion 1 gates the verdict.** A run that did not end alive is invalid.
- **Every result row carries the fingerprint its runs recorded**, which `run.py`
  writes into `meta.json` at run time rather than anyone typing it.

---

## Part 2 — the three lifecycle questions

First batch 2026-08-12, 15 runs, `[surface f7672aba]`.

```
r1-interrupted-resume       5/5 correct    exact 95% CI [0.478, 1.000]
r2-successive-corrections   0/5 correct    every run lapsed at least once
r3-conflicting-leaves       5/5 correct    [0.478, 1.000]
```

### `r1` — recovery after an interrupt

The interrupt landed at 5, 8, 10, 10 and 11 tokens of 12, and the runner
truncated two entries from the log every time, so the memory-versus-disk
divergence the scenario exists to create was real in every run and differently
sized in each. All five ended with the twelve tokens once each in queue order.

**The design point**: "no duplicate writes after an interrupt" is a claim a
do-nothing run passes, which is the failure the criteria document was written to
stop. Truncating the log makes both outcomes positive facts in one artifact — a
run that resumes from memory leaves a hole exactly there, one that reconciles
against the file does not. Turn 2 states only that the process was killed; it
deliberately does **not** say "treat the disk as the only record", which would
turn the measurement into an instruction-following check.

Recorded and not graded: all five read the log before writing to it. The
contract never says to re-read state after an interrupt, and scoring a rule
nobody wrote is how a fixture starts measuring its author's preferences.

### `r3` — conflicting leaf results

Exactly two dispatches per run, both returning, and the per-leaf transcripts
confirm each leaf saw one authority only. Both clause tokens reached the verdict
in all five, so no run resolved the disagreement by dropping half of it.

**The design point**: each authority carries a clause id appearing in no other
file, and the graded question is whether both survived. s8's `a19` showed a
grader keyed on words like `conflict` marking down an answer that described the
conflict without using them; a token check cannot make that mistake.

### `r2` — successive corrections

Every run lapsed, but the per-turn table is the result:

```
turn 1  reached 5, no DECISION line 2, consequence table 0
turn 2  reached 5, no DECISION line 1, consequence table 0
turn 3  reached 5, no DECISION line 5, consequence table 5
turn 4  reached 5, no DECISION line 1, consequence table 0
turn 5  reached 5, no DECISION line 1, consequence table 1
```

The pre-registered test was decay — lapses concentrating in turns 4–5 against
1–2, Fisher exact. **p = 1.000**, 2 of 10 late against 3 of 10 early. Recorded
as *no decay detected at n=5*, which is not the same as "the contract holds".

The obligation graded is the deployed contract's own words: `Mark a material
choice made without user input as DECISION: <what and why>`. Nothing was
invented for the fixture, and a turn that asked instead of choosing never met
the clause's precondition and is not counted against it.

What the run-level 0/5 reflects is turn 3, and that took four more scenarios to
understand.

---

## Part 3 — chasing one request across four scenarios

Turn 3 lapsed in every run. Three explanations were built and killed.

### Killed: crowding out (`r2b`)

The association was clean — every turn-3 reply carried a consequence table
against one of the other twenty, Fisher p = 0.0225 — and it would have read as a
mechanism in any document quoting it. But in that data "has a table" and "is
turn 3" were the same variable.

`r2b-defused-cap` changed one numeral: the cap at turn 3 became 3000 instead of
300, so it no longer swallows the top bracket. Both forks survive; only the
drama goes. The arithmetic is checkable without running anything.

```
turn-3 consequence table   r2 5/5 -> r2b 1/5    Fisher p = 0.0476   manipulation landed
turn-3 DECISION lapse      r2 5/5 -> r2b 5/5    Fisher p = 1.0000   outcome unmoved
```

**Refuted.** Two runs produced no table anywhere across five turns and lapsed on
turn 3 regardless. Killable only because the mediator was measured on every turn
rather than where the hypothesis expected it — that is what separates "the
manipulation didn't land" from "it landed and nothing happened".

### Killed: position (`r2c`)

`r2c-cap-first` moves the cap request to turn 1, other four in relative order.

```
the cap request, wherever it sits   r2 5/5 at turn 3    r2c 5/5 at turn 1
turn 3, whatever sits there         r2 5/5 (cap)        r2c 0/5 (integer cents)
```

Fisher exact **p = 0.0079** on the second row, and every `r2c` run's first lapse
is turn 1. **The lapse follows the request, not the position** — 5 and 0, not 4
and 1.

It also refuted crowding-out a second time from a direction `r2b` could not
reach: in `r2c` the tables moved to turns 2 and 3, which lapsed in none of ten
opportunities, while the cap turn produced no table and lapsed in all five.

### Killed: the choice never surfaces (`m1`, `m3`)

Hypothesis: the cap's forks are settled inside the code being written, while
turn 4 asks in so many words for "an explicit behaviour" and lapses in 1 of 15.

`m1-cap-embedded` tested a single-turn reduction first and **put it in doubt**:
3 of 5 lapsed where the five-turn context lapses 5 of 5, Fisher p = 0.444, which
n=5 cannot separate. The reduction was abandoned rather than assumed, and
`m2-cap-surfaced` was never run — a result from a form not known to be the
phenomenon answers a different question cheaply.

`m3-cap-surfaced-in-context` carried the manipulation into the five-turn
context: `r2`'s turns byte-identical except turn 3 gains one sentence naming the
cap-versus-rounding order. No delegation in it — "you decide" would measure
compliance instead.

**Turn 3 lapsed 5/5. Refuted as filed.**

And the manipulation check found what the design missed. All five engaged the
sentence, and two proved the named fork is not a fork: `min(round(x*r), 300)`
and `round(min(x*r, 300))` are identical when rounding is monotone and 300 is a
fixed point. Exhaustively checked over every amount from 0 to 20000 cents
against all four rates — **zero cases differ**. They were right and the sentence
was wrong, so what got tested is what happens when a request points at a
consequence that does not exist. The filed verdict stands and the qualification
sits beside it; a pre-registration that can be softened afterwards is not one.

### What survives

```
the cap request, no DECISION line   20 of 20 runs     exact 95% lower bound 0.832
the other four requests             15 of 60
```

Position does not move it, dramatic consequence does not move it, and naming a
fork does not move it — not even one the runs then disprove. A clean next test
needs a fork that is provably material, and the fixture has one in plain sight:
every run invents a name for the constant, a choice with no right answer that
the code cannot settle, and none of them marked that either.

---

## Part 4 — the dispatch clause, `d1`/`d2`

The question s11 built `b1` to ask and could not: does a contract clause naming
a skill do anything the skill's own `description` does not, on the dispatch
path? Arms are s11's, built by its `arms.py`; the decision rule is s11's.

21 runs, `[surface f6a99ff0]`.

```
cell                   arm A       arm B       arm C     contract mentions
d1-two-reviews       5/5 loaded  5/5 loaded  5/5 loaded      2 -> 1 -> 0
d2-one-small-edit    0/2 loaded  0/2 loaded  0/2 loaded      2 -> 1 -> 0
```

`summarise.py` shows `d1-two-reviews` at 10 runs, not 5: seeds 6-10 ran later
under a different fingerprint for the criterion-3 observation in Part 6 and are
**not part of this comparison**. The arm comparison is seeds 1-5 against arms B
and C.

Every one of the fourteen swapped runs passed its manipulation check before
being paid for: `NO` to "does your contract contain an explicit instruction to
load `baton-dispatch`" in all of them, against `YES` in arm A, with the contract
hash and surviving mention count recorded per run. No run was invalid.

**With every mention deleted from the contract, the skill loads 5/5 where a
dispatch is going ahead.** By the separation rule filed in advance this is *no
separation*, and the flat kind: three arms identical at ceiling. s11 measured 90
runs on two other clauses and wrote that its conclusion did not extrapolate to
the dispatch path. It does.

Arm C is nearly a clean name removal here — it deletes one parenthetical from
the reporting rule and leaves the obligation — which is cleaner than the arm C
s11 had to build for `provider-routing`.

**Three things this does not say**: not that the skill is unnecessary, since the
description was never manipulated; not that the clause is safe to delete, only
that whoever argues it is necessary now owes a condition where it carries
something; not that `b1`'s fixtures were the problem — they never were.

---

## Part 5 — contract against client instruction, `p1`–`p4`

Direction 1 had been undecided since 2026-08-08 for want of session evidence:
its refutation condition is a case where a client instruction and the contract
contradict each other and the contract still wins. That was read as needing to
wait for one to happen. It does not — it can be built.

25 runs, `[surface 843e9423]`.

```
p1-language         contract wins 5/5    (Chinese prompt)
p1b-language        contract wins 3/5    (English prompt — confound controlled)
p2-code-english     injected wins 5/5
p3-decision-marker  injected wins 5/5
p4-direct-default   injected wins 5/5
```

`p1`'s request is written in Chinese, so a Chinese reply might be mirroring the
prompt. `p1b` removes that: English request, system prompt reading `Never use
Chinese characters in your reply`, contract requiring Traditional Chinese —
three replies came back with 98 to 110 Han characters. Fisher against `p1` is
p = 0.444, so mirroring may contribute; it cannot explain the three.

**The refutation condition is an existence claim, and three exist.** Direction 1
wrote its own downgrade in advance — *"成立就只保留 user-context 這個事實, 不寫
優先權結論"* — and that has been applied: the claim that the resident contract
gets weight rather than force is struck, and what remains is the observable
half, that it arrives as user context with compliance that is probabilistic
**and rule-specific**.

**Three limits stay attached.** Three of four rules lost 5/5, so this is not
"the contract wins". `--append-system-prompt` appends where a real client
instruction is authored, which makes a contract win strong evidence and a
contract loss weak. And the manipulation was checked *after* the batch, at 10 of
10 under identical flags — s11 has run a per-arm check since 2026-08-08 and this
did not, in the cell where the burden was highest.

---

## Part 6 — criterion 3, the least stable thing here

```
d1 seed 1-5   4/5     d1 arm B  4/5     r3   3/8
d1 seed 6-10  1/5     d1 arm C  3/5     p4   0/5     pooled 15/33 = 45%
```

Same contract, same scenario, same configuration, 4 of 5 and then 1 of 5.
**Criterion 3 is not measuring a stable property; it varies run to run by more
than any manipulation in this directory has moved anything.**

The failures split three ways, and only one is discipline:

| shape | how often | reachable by |
|---|---|---|
| logged with an id that ties to nothing | 2 of 23 pre-fix, 1 of 5 after | tooling — fixed twice, below |
| `experience-log` invoked and rejected on arguments | 1 of 23 | tooling |
| never invoked at all | 3 of 5 in the last batch | neither: no message changes a command that is not run |

**Two fixes landed, and their limit is instructive.** 2026-08-13:
`experience-log` reports when `--dispatch-id` matches no staged stub. 2026-08-14:
a replay run read that note twice, filed both records under an agent id with the
session prefix dropped, and moved on — so the note now offers the right id when
exactly one staged stub has that agent segment. **Making an error visible is not
making it fixable**, and neither fix reaches the dominant failure.

---

## Part 7 — instruments were wrong more often than sessions were

Six, all caught, all negative-controlled and tested afterwards. This is the part
worth reading if you inherit this directory.

| instrument | what it got wrong | how it was caught |
|---|---|---|
| `DECISION:` matcher | scored `r2` **0 of 5** when four of five turns had emitted the marker decorated as ``**`DECISION:` …**`` | reading raw replies instead of the verdict |
| criterion 1 | computed and then ignored by the verdict, so a run killed mid-529-retry scored `incorrect` | reading a verdict that made no sense |
| fault detector | matched the bare words `Overloaded` and `rate limit`, reporting a fault in a healthy run — the phrase sat in a skill reference the agent had read | its first outing |
| criterion 3 | counted only staged stubs, so "fully reconciled" and "never dispatched" were the same number, both reading as good news | comparing telemetry files by hand, after a wrong sentence had already been reported |
| batch resume guard | skipped a seed whose directory existed but held nothing, silently taking n from 5 to 4 | a results table with four rows where five were expected |
| surface stamps | typed by hand three times, wrong twice | recomputing before committing |
| this README's own run count | typed as 82 where the directory holds 92 | counting the directories while checking the rewrite |

**Two of these produced a clean, quotable, entirely false finding before being
caught, and the last one is in this file.** The pattern is the same every time: a checker keyed on the shape of an
artifact rather than its substance. What worked was reading raw output rather
than verdicts, measuring mediators everywhere rather than only where the
hypothesis expects them, and moving anything hand-typed into the artifact —
`run.py` records its own surface fingerprint, `summarise.py` regrades rather
than reading a stale `verdict.json`.

---

## What this construct cannot support

- **The contract and the hooks cannot be separated** (measured), so no result
  here attributes an outcome to the contract alone.
- **An interrupt at a wall clock is not deterministic.** The marker, not the
  runner, decides whether a run counts, and a batch is expected to contain
  invalid runs.
- **One machine, one model family.** The agent under test shares a prior with
  whoever wrote the contract.
- **`r2`'s five corrections are a construct**, and a constructed correction is
  more legible than a real one. A lapse observed here is a floor.
- **`r2` runs cannot execute tests.** The allowlist grants reads under the skill
  trees and the ledger script, nothing else, so every run says it could not
  verify its own edits. It does not touch the graded obligation, but the agent
  under test is editing code it has never run.
- **`--append-system-prompt` approximates the client position**, appending where
  a real client instruction is authored.

## Open

- **The grader gates on criteria 1 and 2 only.** The criteria document says all
  four must hold before a result may be cited, and criterion 3 held in 15 of 33.
  Either the document overstates the bar or the results above overstate their
  standing; that is a decision, and it is not made here.
- **`p1` needs a per-run manipulation check**, not a batch-level one.
- **The cap request's 20 of 20 has no explanation** that survived contact. The
  next test needs a provably material fork; the constant's name is the candidate.
- **Criterion 3 at 45%** is a decision rather than a measurement problem:
  enforce it, accept it, or remove the need for it by having the hook file a
  provisional record the session revises.
- **Nothing here measures whether a rule firing makes the work better.** `d1`
  loaded the skill 5/5 in all three arms and nobody compared their dispatch
  quality. Filed in the verification gaps of `docs/research/README.md`.
