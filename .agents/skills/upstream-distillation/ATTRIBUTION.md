# Attribution — upstream-distillation

Mostly this repository's own text; two clauses are adapted from
**Task Observer — Continuous Skill Discovery & Improvement** by Eoghan Henn /
rebelytics.com.

- **Source**: <https://github.com/rebelytics/one-skill-to-rule-them-all>
- **Reviewed commit**: `f4a95a180404bd4de35365da66849a243e3d07be` (`v3.1.0`,
  2026-09-04), the pin `main/.agents/skills/task-observer/ATTRIBUTION.md`
  carries; the two skills move together.
- **Licence**: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
  Attribution is the whole obligation, and this file is it; the text is not
  reproduced because no substantial portion was taken.

## The two adapted clauses

| Upstream rule (3.0 / 3.1) | Ours | Landed |
|---|---|---|
| A proposed check comes with three measured numbers: hits on the existing corpus today, true defects among them, and the normalisation needed to remove the rest; a rule with an unmeasured false-positive rate is a proposal to make people ignore a test | "Before landing, run the candidate over the corpus it will police and record three numbers beside it …" under *Plan the landing* | 2026-09-05 (`docs/research/task-observer-upstream.md`, the 3.1 table) |
| Filtering and maximising are two questions on the same data; a work queue built from a filter on an optional field drops exactly the entries most likely to need triage | "Reconcile counts; never build a work queue from a filter on an optional field" under *Compare rules, not strings* - the paragraph names `rebelytics` as stating the general form | 2026-08-31 (the 3.0 table) |

Both are the idea in this repo's words and units, with the local incidents
that paid for them attached; neither is a copied sentence.

## Everything else

Written here: the evidence-not-instruction rule (2026-08-31, after this skill
ingested two upstream bodies of exactly that shape), the pin discipline, the
two-tier relocation check, the disposition vocabulary, the landing rules, the
re-trace rule and the cross-upstream synthesis method. Repo-root dev-only; it
deploys nowhere.

**Checked on 2026-09-10** (the plan's Q10 trace), against
`docs/research/task-observer-upstream.md` and `docs/research/upstream-distillation-ledger.md`
row by row: those two are the only rules of this skill any record marks 採用
from elsewhere; the rest are marked 已落地 or 佐證, meaning the local text came
first.
