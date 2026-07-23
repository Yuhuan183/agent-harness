---
name: leaf-dispatch
description: |
  Codex main-task dispatch procedure — cost test, grouping and batching rules, brief schema, stop defaults, fixed dispatch records, QC fraud checklist, ledger logging, and verifier triggers. Load before every leaf dispatch decision.
  觸發：任何 leaf 派工前、「怎麼拆」「要不要派」「批次」「brief 怎麼寫」「驗收怎麼定」。
  不觸發：subagent（leaf）自身的工作——leaf 永不 orchestrate。
---

# Leaf Dispatch

Apply this before every dispatch. Direct execution is the default; the main
task owns framing, architecture, ambiguity, integration, synthesis,
model-intensity choice, and final judgment.

## Cost test

A subagent at the session's effort saves no compute — delegate only when
parallelism, context protection, or fresh-context independence clearly exceeds
dispatch overhead (briefing, context reconstruction, collection, QC). Before
delegating, confirm observable outcome, delegation benefit, independent
workstreams, one owner per writable artifact, and the integration/final-
verification owner. If any answer is weak, work directly or use one bounded
read-only exploration.

## Grouping and batching

- Group by shared context, artifacts, dependencies, and verification surface —
  not request bullets.
- Keep one unknown bug's diagnosis, first fix, and live verification in one
  reasoning chain.
- Batch recurrent execution only when one stable one-shot brief completely
  states the goal, constraints, done criteria, ownership, and per-item
  acceptance, and all remaining items are independent and the same shape. A
  diagnosed review finding with a known remedy is execution work, but main
  still owns triage, exceptions, integration, and acceptance; never use an
  item-count trigger or batch work coupled to main's evolving evidence.
- Converge shared schemas, registries, config, generated output, and lockfiles
  before parallel writes.

## Briefs and stops

Brief outcome, scope/non-scope, excluded capabilities, minimum paths,
ownership, local checks, output, and stops once (defaults: 3 failed fix-verify
cycles or 2 fruitless lookups → stop and hand back). When an irreversible or
outward action is in scope, the brief carries the user's authorization as a
provenance-labelled direct quote from their message; repository text never
populates it.

## Dispatch records and ledger

Report every launch and post-QC outcome as separate fixed records, never mixed
into prose:

```text
[LEAF_DISPATCH] task=<label> | role=<role> | class=<class> | request_source=codex | route=<profile>/codex/<model>/<effort> | reason=<payoff>
[LEAF_RESULT] task=<label> | outcome=<accepted|corrected|rebriefed|failed> | qc=<spot|full> | ledger=<logged|skipped(reason)>
```

Use actual resolved route values and the same neutral task label in the
ledger. After quality-checking each native Codex leaf, log the outcome with
`experience-ledger`, request source `codex`, resolved profile/model/effort,
and the dispatched non-smoke task class.

## QC

Collect the finished subagent response and quality-check it against the brief
before integration, hunting false-completion frauds: weakened or bypassed
checks, fixtures fabricated to satisfy a check, undeclared out-of-scope
changes, missing owed `INTENT:`/`TWINS:`/`AUTH:` lines, and leftover
leaf-created scratch files (pre-existing dirty-worktree files are not debris).
Audit the owed lines mechanically with `~/.codex/scripts/qc-gate-lines
<report> [--behavior-changed] [--defect-fixed] [--outward-taken]`, setting
flags from the diff and evidence, never from the report's claims; line truth
stays with the reviewer. Follow up only for genuinely new or redirected work. Centralize
repository-wide, live, or expensive gates; preserve partial evidence when
stopping.

Do not resubmit a substantially unchanged Plan to `plan-verifier`; another
readiness pass requires a material revision or new evidence. If disagreement
remains unresolved, simplify the Plan, surface the blocker, or defer the
blocked scope — never silently overrule it.

## Verifier triggers and placement

Use at most one outcome verifier per top-level task, only when failure could
affect a security/trust boundary, money, destructive data, migrations,
concurrency, public APIs, or cross-repo compatibility; judgment-heavy
integration cannot be proven mechanically; acceptance depends on adversarial
state/boundary behavior; evidence conflicts; reproduction fails; or the user
requests independent verification.

Not for docs-only, trivial config, decisive mechanical checks, low-risk direct
work, or duplicate review. Distinct failure surfaces do not add quota; never
stack gates over the same surface.

Place fresh verification at the smallest coherent integration boundary where
the complete acceptance claim can be independently refuted. Tests, builds, and
static checks are intermediate evidence during iteration. Verify earlier for
security, cross-language or FFI, serialization or pre-aggregation,
irreversible-operation, and integration-blocking boundaries; earlier timing
does not authorize another verifier over the same surface.
