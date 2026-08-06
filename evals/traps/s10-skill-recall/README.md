# s10-skill-recall trap (selection-trap)

Fourth behavioral trap, and the first aimed at something happening *before* a
skill runs. `s7`/`s8`/`s9` all begin with the agent already inside the work.

**What it measures, exactly: whether a description discriminates the asks it
should and should not take, when an agent reads it deliberately.** It does not
observe skill loading. The brief is a batch classification task — all six
descriptions and all eighteen utterances in front of the agent at once, the
answer format given — and `grade.py` reads `SELECT:` lines, not invocation
events. Real auto-selection is a harder condition: one opening message, the
description competing with a whole system prompt, nobody having asked "which
skill applies". Reading a passing arm as "routing still works" is the mistake
this paragraph exists to prevent (2026-07-31 review, which named the overclaim
in the first version of this file).

That makes the evidence asymmetric, and the asymmetry is what the arms are for:

- **A failing arm is strong.** A description that cannot discriminate under the
  easy condition certainly cannot under the hard one. Arm D's result stands.
- **A passing arm is weak.** Discriminability is necessary, not sufficient. B
  and C passing does not license either trim.

The gap it addresses is still concrete. A skill description is permanent
resident cost **and** the only surface that routes work to that skill, so the
word budget pushes it shorter while recall pushes it longer. On 2026-07-30 a
`speak-human-tw` trim was measured — 19 words, ~2% of the resident tier — and
dropped, because nothing here could say what it cost. This trap is a lower
bound on that cost, which is more than nothing and less than a routing test.

## Layout

| Path | Role | Show to agent under test? |
|---|---|---|
| `pristine/descriptions.md` | generated: the six resident descriptions, as a session carries them | arm A: yes (as a fresh copy) |
| `pristine/utterances.md` | the eighteen opening messages | yes |
| `variants/*.md` | arm B/C/D surfaces, one lever each | that arm only, as `descriptions.md` |
| `GROUND-TRUTH.md` | item design, answer rationale, failure modes, A/B protocol | never |
| `grade.py` | mechanical answer sheet (decisions + read-only discipline) | never |
| `build.py` | regenerates the bundle from the live frontmatters | — |
| `briefs/arm-a-leaf-brief.md` | verbatim dispatch text, identical for every arm | yes |

The bundle is **generated**, not copied: `python3 build.py --check` fails once
the checkout's descriptions move past it, and the repo suite runs that check. A
trap graded against last month's routing surface measures nothing.

## Protocol (arm A)

1. `python3 build.py --check` — refuse to run against a stale surface.
2. Copy `pristine/` to a scratch workdir (inside the project root for bridge
   dispatches — Codex `apply_patch` is confined to it).
3. Dispatch `briefs/arm-a-leaf-brief.md` verbatim; capture the final report.
4. `python3 grade.py --workdir <copy> --report <report file>` — exit 0 only when
   the decisions are exactly U01–U18 and all match, nothing was written
   anywhere under the workdir, and the surface is recognised. `--json` for a
   machine-readable summary.

For a rung other than the role's deployed pin, or for any run that must not
reach the operator's proxy, dispatch through `evals/scripts/rung-run.py`
rather than the Agent tool. It puts `--model` and `--effort` on the command
line of its own `claude --print` process and runs outside every project, so no
deployed pin is edited and no project `env` block re-attaches the proxy. Those
runs are sessions, not subagents, so their ledger records are `explicit`.

Arms B/C/D are the same brief over a workdir whose `descriptions.md` was
replaced by that arm's variant. Three samples per arm minimum; one sample cannot
separate a discrimination defect from run-to-run variance. Lever table and
rationale: `GROUND-TRUTH.md`.

## What the codes mean

`R1-missed-critical` and `R2-overtriggered-critical` are the two the trap exists
for. Recall-critical asks (U02, U05) match only through a document kind, with no
quoted trigger phrase — they are what an enumeration trim costs.
Precision-critical asks (U09, U10, U11) each carry a verbatim trigger phrase
attached to work the 不觸發 clause rules out — they are what an exclusion trim
costs. A `-critical` finding is the trap working, not a fixture to tune.

Self-test after any fixture edit (eight verified 2026-07-30, four more
2026-07-31): a perfect sheet exits 0; a sheet with the three precision items
flipped raises exactly `R2-overtriggered-critical` ×3; a one-line report raises
`R4-missing` ×17; an empty report is refused by the argument parser; a variant
surface is named rather than flagged; a hand-edited surface raises
`S2-surface`; an appended `utterances.md` raises `S1-edited`; an invented skill
name raises `R5-malformed`. Added after a review found each reaching exit 0: a
nineteenth `SELECT:` line raises `R5-malformed`, and a created
`nested/report.md`, `sub/descriptions.md` or any other file raises `S1-added` —
the two exempt names are matched as exact paths, not basenames at any depth.
`test_the_selection_grader_exit_zero_means_what_it_claims` runs these four.

**Ledger hygiene.** Log every trap dispatch with `--class smoke` (excluded from
route-preference decision counts).

## Surface re-cut, 2026-08-06

Every surface now opens on the same line. Until this date the generated
bundle announced itself as `GENERATED by build.py` and each variant named the
clause it was missing — variant C's label even pointed at `GROUND-TRUTH.md`.
Two of that day's arm-D runs quoted their label back, one reasoning explicitly
that the header flagged both clauses as removed and that it still answered
`none`. A surface that tells the agent which arm it is in cues the agent to
compensate, which biases the defective arms towards passing.

What that costs the rows below. Every arm-B/C/D row dated on or before
2026-08-06 was graded under that cue and should be read as a lower bound on
the defect, not a rate: a failure there is still a failure, but a pass is
weaker than it looks. Arm-A rows lose only a neutral provenance line, so they
carry over. Byte-for-byte the old surfaces no longer exist, so no future run
is comparable to a pre-recut row on the surface hash alone.

## Results log

| Date | Agent / route | Arm | grade.py | Notes |
|---|---|---|---|---|
| 2026-07-31 | `explore` claude-sonnet-5/low — a1/a2/a3 | A (control) | 0 findings ×3 | Baseline established: 18/18 ×3. Every run named the clause it decided on. |
| 2026-07-31 | `explore` claude-sonnet-5/low — b1/b2/b3 (first cut) | B (defective) | 0 findings ×3 | **Void for precision.** That `b-trimmed.md` dropped the zh-TW exclusion but left the English `Not for: … code/log/config`; all three runs cited the surviving English clause by name, so U09–U11 tested nothing. Recall half stands: U02/U05 correct 3/3 without the document kinds. |
| 2026-07-31 | `explore` claude-sonnet-5/low — b1/b2/b3 (re-cut) | B | 0 findings ×3 | Document kinds removed, exclusions intact both languages. U02/U05 3/3 — each run generalised from `檢查對外文字的語感`. **Dropping the seven document kinds cost no recall on this item set.** |
| 2026-07-31 | `explore` claude-sonnet-5/low — c1/c2/c3 | C | 0 findings ×3 | Exclusions removed in both languages, document kinds intact. U09–U11 3/3 correct — every run reasoned from the positive scope (`對外文字` plus the listed kinds) instead. **The exclusion clause was not load-bearing while the enumeration was present.** |
| 2026-07-31 | `explore` claude-sonnet-5/low — d1/d2/d3 | D (both) | `R2-overtriggered-critical` ×3 on d1; 0 findings on d2/d3 | **The trap fired.** With neither clause, d1 routed all three of nginx-config, error-log and Python-code asks to `speak-human-tw` on the literal `改自然一點`/`說人話` match. d2/d3 held the line on `對外文字` alone but both flagged U09–U11 as the most ambiguous group and said a different reasonable reading selects the skill. 1/3 failure at 3 samples is a floor, not a rate. |
| 2026-08-06 | `explore` claude-sonnet-5/low — son1/son2/son3 | A (control) | 0 findings ×3 | Same-day control for the rung A/B below; 18/18 ×3, unchanged from 2026-07-31. |
| 2026-08-06 | `explore` **claude-opus-5/low** — opu1/opu2/opu3 | A | 0 findings ×3 | First run of this fixture on a second rung, through the Agent tool's per-dispatch `model` override; every route confirmed from the pending hook's `observed_model`, not from the dispatcher's intent. Both rungs sit at ceiling on arm A, so it separates nothing — which is why arm D was re-cut below. |
| 2026-08-06 | `explore` claude-sonnet-5/low — dson1/dson2/dson3 | D (both) | 0 findings ×3 | Held 3/3 where 2026-07-31 lost d1, confirming that row's own reading of 1/3 as a floor rather than a rate. |
| 2026-08-06 | `explore` **claude-opus-5/low** — dopu1/dopu2/dopu3 | D | `R2-overtriggered-critical` ×3 on dopu3; 0 findings on dopu1/dopu2 | **The higher rung did not hold the line.** dopu3 routed U09/U10/U11 to `speak-human-tw` on the literal `改自然一點`/`說人話` match — the same failure d1 made in July — and said so explicitly: with neither clause left, nothing in the surface rules out code/log/config. dopu1/dopu2 held on `對外文字` alone and both named U09–U11 as their lowest-confidence group. Median wall-clock 37.1s against sonnet/low's 30.6s. AA's per-rung Briefcase Elo puts opus/low 295 points above sonnet/low; at n=6 that gap bought nothing here and the only failure of the twelve was on the higher rung. |
| 2026-08-06 | `explore` claude-sonnet-5/low — rr1/rr2 via `rung-run.py` | A (isolation check) | rr1 `R1-missed` (U16); rr2 0 findings | Not a rung sample — these validated the runner itself. rr1 still reached the proxy, because its `cwd` was the repository and this checkout's untracked `.claude/settings.local.json` re-injects `ANTHROPIC_BASE_URL`; it answered `none` on U16. rr2, run from outside every project, does not appear in the proxy log at all and scored 18/18. One seed each settles nothing about U16; what it establishes is that the isolation now holds. |
| 2026-08-06 | `explore` claude-sonnet-5/low — rds1/2/3 via `rung-run.py` | D, re-cut surface | 0 findings ×3 | First arm-D rows with no label to read and no proxy in the path. |
| 2026-08-06 | `explore` claude-opus-5/low — rdo1/2/3 via `rung-run.py` | D, re-cut surface | 0 findings ×3 | Removing the cue did not make the arm harder for either rung, which is the opposite of what the re-cut was braced for. Across both surfaces the arm-D totals are sonnet/low 6/6 and opus/low 5/6, so dopu3 reads as run-to-run variance rather than a rung effect, and the rung comparison stays where the A/B left it: no advantage measured for opus/low. |

### What the four arms say together

B and C are each clean, and reading that as "cut both" is exactly the inference
they do not support: the two clauses are redundant covers for the same asks, so
removing either alone is absorbed by the other. D removes the redundancy and the
precision failure appears immediately. **The 2026-07-30 decision to leave the
description alone is upheld, for a reason nobody had stated: its length is
partly redundancy that only shows up when you take both copies away.**

Neither B nor C alone is disproven as a trim — and by the asymmetry at the top
of this file, neither is *proven* either: a clean arm here means the clause is
not load-bearing for deliberate discrimination, which is the weaker of the two
things a description has to do. Anyone taking one should take exactly one, and
re-run D-shaped arms before taking the second.

### Validity limits

- **The construct, first.** `grade.py` measures agreement with an answer sheet
  under batch classification, not skill loading in a live session where the
  descriptions compete with a full system prompt and nobody has asked which
  skill applies. A real runtime-selection eval would need one fresh session per
  utterance and provider-side invocation events; it does not exist here. Read
  every arm through the strong/weak asymmetry above.
- One route, one item set, three samples per arm per rung. Two models as of
  2026-08-06 (claude-sonnet-5/low and claude-opus-5/low); effort is still one
  rung, because the Agent tool overrides `model` per dispatch but not `effort`.
- **The variant surfaces announce themselves.** `variants/d-both.md` opens with
  `<!-- VARIANT D: speak-human-tw document kinds AND exclusions both removed. -->`,
  and two of the six 2026-08-06 arm-D runs quoted it back — one reasoned
  explicitly that the header flagged both clauses as removed and that it still
  resolved U09/U11 as `none`. An agent told which clause was cut is cued to
  compensate for the cut, which biases arm D towards passing. Every arm-D row
  in this table, 2026-07-31's included, was graded under that cue. Removing the
  comment re-cuts the fixture and makes the existing rows uncomparable, so it
  is recorded here rather than quietly fixed.
- **Cross-arm bleed observed.** Two arm-D runs' notes referenced description
  copies from outside their own workdir — one named a compression-store hash,
  one named "the Variant B/D copies surfaced via proactive expansion" and
  explicitly set them aside. Both still answered from their own file, and the
  arm that failed did so consistently with its own surface, so the finding
  stands. But arms are not perfectly isolated when the host harness has context
  machinery of its own, and a future run should either disable it or put the
  variants where no expansion can reach them.
