---
name: upstream-distillation
description: |
  Recheck an upstream this repo distils from, classify every rule it carries, and land the result across the right document tiers. Use when rechecking a pinned upstream, surveying a new one, adding or advancing a pin, or asking whether an upstream change is already covered here. Trigger on "重查上游", "蒸餾", "upstream 有沒有更新", "這條我們有沒有", or a new peer project worth surveying. Do not use for reviewing this repo's own design (harness-review), for establishing a claim in general (evidence-ladder), or for reading a changelog you do not intend to act on. Repo-root dev-only; never add it to the deployment manifest.
---

# Upstream Distillation

A distillation is finished when every upstream rule has a disposition and every
disposition is true of the tree. Both halves fail quietly: an unclassified rule
is invisible, and a classification that stopped matching the code reads exactly
like one that still does.

## Find what you are actually comparing against

Fetch upstream. Re-reading our own notes is not a recheck — the ATTRIBUTION
files say so because a same-day reading held in memory once under-credited
upstream in four places.

Locate the pin in this order, and do not stop at the first miss: the skill's
`ATTRIBUTION.md`; the skill body, where the source may be a single sentence; the
research tier. On 2026-08-21 a survey checked the first and third, found
nothing, and reported the skill had no upstream — it was in the second the whole
time.

Three things about pins, each from a specific miss:

- **The pin is a commit, not a release.** `cablate/baton` added a whole section
  after `v0.1.1`; anyone distilling from the tag would have shipped without it.
- **Forks version independently.** `pilotfish` was at v1.3.10 while its Codex
  fork was at 1.7.1. The numbers are not comparable and neither is the content.
- **A pin lives where it resolves.** Full SHA in `ATTRIBUTION.md` and the
  research tier; never a bare short SHA in a deployed file (`docs/README.md`
  rule 9). A dead citation has already survived in a deployed file once because
  a test pinned its string.

## Compare rules, not strings

This repo distils rather than copies, so upstream's wording is mostly absent
here by design. A keyword search therefore under-reports, and its silence looks
like a finding.

Enumerate upstream's rules, then for each one ask whether a local equivalent
exists **in concept**, reading the sections it would live in. Calibrate any
probe before believing it: on 2026-08-21 a shell probe answered "no local
equivalent" for all ten of an upstream's rules, twice, both times from a quoting
bug — the correct answer was eight of ten covered.

## Give every rule a disposition

One of: **已落地** (already true here), **採用**, **改造後採用**, **不採用**
with the reason, or **佐證** — upstream evidence for something already decided.
A rule left unclassified is the one that goes missing.

Two dispositions people skip:

- **"Upstream did not move" is a result.** Record the date and the last commit.
  Without it, "did not change" and "was not checked" are the same sentence.
- **佐證 is worth writing down.** An independent implementation reaching our
  design is stronger evidence than our own reasoning, and an upstream that
  defines a tier and leaves it empty tells you more than one that fills it.

## Weigh before adopting

Raise the weight when two independent upstreams point at the same gap, or when
an upstream publishes its own negative results — a project that scores its own
feature 5/10 in a release note has earned trust on the numbers it does like.

Lower it when the rule assumes a shape this repo does not have, and say which
shape rather than "not applicable". Prefer the intersection of two upstreams'
answers plus the sharpest clause either one adds; that is a smaller rule than
either and it carries both arguments.

## Land it in the same pass

Adopt and implement together, or the record lies. On 2026-08-21 a table said
"gap, recommend adopting" for a rule that had landed hours earlier in the same
session.

Where each part goes:

- **Guidance tier** — only the rule, in this repo's words and units. Adding to a
  budgeted file needs displacement, or a deliberate raise carrying the
  measurement and the reason.
- **Evidence tier** — the dated survey, the full SHA, the per-rule disposition
  table, and what was checked to decide it.
- **`ATTRIBUTION.md`** — pin, licence, and what was taken, rewritten, dropped,
  or added. Say plainly what was *not* classified rather than implying a full
  audit.
- **Currency table** — version, check date, and what to watch for next time.

Then re-run the suite: skills on the prompt surface need
`scripts/prompt-surface-census.py --write`, and a changed contract phrase may be
pinned by a test that will tell you.

## Known limit

`scripts/upstream-recheck.sh` and `docs/research/upstream-distillation-ledger.md`
cover exactly one upstream. Every other recheck is manual, including all three
done on 2026-08-21. Generalising the script is unfinished work, not an oversight
to hide — until it is done, this skill is the procedure and a person is the
mechanism.
