# s10-skill-recall trap (selection-trap)

Fourth behavioral trap, and the first that measures something happening
*before* a skill runs: whether the routing surface loads the right skill at all.
`s7`/`s8`/`s9` all begin with the agent already inside the work.

The gap was concrete. A skill description is permanent resident cost **and** the
only surface that routes work to that skill, so the word budget pushes it
shorter while recall pushes it longer. On 2026-07-30 a `speak-human-tw` trim was
measured — 19 words, ~2% of the resident tier — and dropped, because nothing
here could say what it cost. This trap is that measurement.

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
   all eighteen decisions match, nothing was written, and the surface is
   recognised. `--json` for a machine-readable summary.

Arms B/C/D are the same brief over a workdir whose `descriptions.md` was
replaced by that arm's variant. Three samples per arm minimum; one sample cannot
separate a routing defect from run-to-run variance. Lever table and rationale:
`GROUND-TRUTH.md`.

## What the codes mean

`R1-missed-critical` and `R2-overtriggered-critical` are the two the trap exists
for. Recall-critical asks (U02, U05) match only through a document kind, with no
quoted trigger phrase — they are what an enumeration trim costs.
Precision-critical asks (U09, U10, U11) each carry a verbatim trigger phrase
attached to work the 不觸發 clause rules out — they are what an exclusion trim
costs. A `-critical` finding is the trap working, not a fixture to tune.

Self-test after any fixture edit (all eight verified 2026-07-30): a perfect
sheet exits 0; a sheet with the three precision items flipped raises exactly
`R2-overtriggered-critical` ×3; a one-line report
raises `R4-missing` ×17; an empty report is refused by the argument parser; a
variant surface is named rather than flagged; a hand-edited surface raises
`S2-surface`; an appended `utterances.md` raises `S1-edited`; an invented skill
name raises `R5-malformed`.

**Ledger hygiene.** Log every trap dispatch with `--class smoke` (excluded from
route-preference decision counts).

## Results log

| Date | Agent / route | Arm | grade.py | Notes |
|---|---|---|---|---|
| 2026-07-31 | `explore` claude-sonnet-5/low — a1/a2/a3 | A (control) | 0 findings ×3 | Baseline established: 18/18 ×3. Every run named the clause it decided on. |
| 2026-07-31 | `explore` claude-sonnet-5/low — b1/b2/b3 (first cut) | B (defective) | 0 findings ×3 | **Void for precision.** That `b-trimmed.md` dropped the zh-TW exclusion but left the English `Not for: … code/log/config`; all three runs cited the surviving English clause by name, so U09–U11 tested nothing. Recall half stands: U02/U05 correct 3/3 without the document kinds. |
| 2026-07-31 | `explore` claude-sonnet-5/low — b1/b2/b3 (re-cut) | B | 0 findings ×3 | Document kinds removed, exclusions intact both languages. U02/U05 3/3 — each run generalised from `檢查對外文字的語感`. **Dropping the seven document kinds cost no recall on this item set.** |
| 2026-07-31 | `explore` claude-sonnet-5/low — c1/c2/c3 | C | 0 findings ×3 | Exclusions removed in both languages, document kinds intact. U09–U11 3/3 correct — every run reasoned from the positive scope (`對外文字` plus the listed kinds) instead. **The exclusion clause was not load-bearing while the enumeration was present.** |
| 2026-07-31 | `explore` claude-sonnet-5/low — d1/d2/d3 | D (both) | `R2-overtriggered-critical` ×3 on d1; 0 findings on d2/d3 | **The trap fired.** With neither clause, d1 routed all three of nginx-config, error-log and Python-code asks to `speak-human-tw` on the literal `改自然一點`/`說人話` match. d2/d3 held the line on `對外文字` alone but both flagged U09–U11 as the most ambiguous group and said a different reasonable reading selects the skill. 1/3 failure at 3 samples is a floor, not a rate. |

### What the four arms say together

B and C are each clean, and reading that as "cut both" is exactly the inference
they do not support: the two clauses are redundant covers for the same asks, so
removing either alone is absorbed by the other. D removes the redundancy and the
precision failure appears immediately. **The 2026-07-30 decision to leave the
description alone is upheld, for a reason nobody had stated: its length is
partly redundancy that only shows up when you take both copies away.**

Neither B nor C alone is disproven as a trim. Anyone taking one should take
exactly one, and re-run D-shaped arms before taking the second.

### Validity limits

- One route, one model, one item set, three samples per arm. `grade.py`
  measures agreement with an answer sheet, not selection behaviour in a live
  session where the user can clarify.
- **Cross-arm bleed observed.** Two arm-D runs' notes referenced description
  copies from outside their own workdir — one named a compression-store hash,
  one named "the Variant B/D copies surfaced via proactive expansion" and
  explicitly set them aside. Both still answered from their own file, and the
  arm that failed did so consistently with its own surface, so the finding
  stands. But arms are not perfectly isolated when the host harness has context
  machinery of its own, and a future run should either disable it or put the
  variants where no expansion can reach them.
