---
name: harness-review
description: |
  Repo-internal deep design review of agent-harness across six fixed dimensions (logic chain, flow, language, wording, modularity, fixed overhead).
  觸發：「深度 review」「harness review」「審一下這個 repo 的設計」、大型 merge 前後的契約／routing／機制稽核。
  不觸發：其他 repo 的產品程式碼 review、單檔修改、例行測試。Dev-only: lives in dev/, never deployed by the manifest.
---

# Harness Deep Review

Read-only design review of this repo's contracts, routing, and mechanisms.
Deliverable: ranked findings plus a per-dimension verdict. Never fix during the
review; fixes are a separate task with their own scope.

## Method

1. **Inventory first** — sizes and language ratios ground three dimensions
   before any judgment (commands in [references/probes.md](references/probes.md)).
2. **Dual-provider is the default shape** — this is judgment-dense, so offer the
   three-option gate (`Dispatch GPT + Claude` recommended). Main session always
   does its own full pass and owns synthesis; the GPT pass is an independent
   read-only lens via the codex bridge (`verifier` role, `quality-guarded`,
   class `review`). Check `codex-usage --quota` (short window first) before
   dispatching. Bridge operations have known traps — see
   [references/probes.md](references/probes.md) § Bridge.
3. **Spot-verify before accepting** — independently reproduce every high-severity
   finding and a sample of mediums (grep/read only). A finding that fails
   reproduction is dropped, not softened.
4. **Log the dispatch** — `LEAF_DISPATCH`/`LEAF_RESULT` records and an
   experience-ledger entry (class `review`) are mandatory, not optional polish.

## The six dimensions

Each has a core question and a signature failure mode observed in this repo:

1. **Logic chain** — does every stated control have an enforcing mechanism?
   Signature: policy verbs (block/reject/enforce) backed by a fail-open hook
   that cannot reject; two files answering the same routing question
   differently; tools that depend on deployed HOME state to pass the very
   preflight that gates deployment (bootstrap self-dependency).
2. **Flow / diagrammability** — can each policy be drawn as a closed DAG?
   Signature: prose invariants with no carrying field (single-hop fallback but
   no hop/origin fields anywhere); feedback loops that stop at "suggestion"
   with no approval→apply edge.
3. **Language policy** — runtime, agent-consumed text is English; human-facing
   docs are zh-TW. Signature: a runtime skill written in Chinese; PRC variants
   (后/软件/信息) leaking into zh-TW prose; mixed-language shell comments.
4. **Wording precision** — one term, one meaning, defined once. Signature:
   cardinality rules stated three ways (exactly one / at most one / stack);
   the same field name meaning three things; load-bearing acronyms never
   expanded (CP-first).
5. **Modularity / sharing** — single source per concern, correct ownership.
   Signature: twin role contracts hand-copied with no semantic parity test;
   personal preferences inside portable settings; artifacts deployed that no
   runtime reads (tests/plans/examples in HOME).
6. **Fixed overhead** — resident payload minimal and budgets ungameable.
   Signature: one platform resident-heavy while the other externalizes the
   same content to skills; line-count budgets defeated by long lines; hooks
   re-probing on every session what a cache could answer.

## Output contract

- Findings as `F-NN` blocks: severity (high/medium/low), dimensions hit,
  `file:line` evidence, one-sentence defect, smallest concrete fix.
- Ranked by severity; end with SOUND / NEEDS-WORK per dimension plus one line
  of reasoning.
- Final user report in zh-TW, merged across providers, deduplicated, with a
  prioritized fix list. Do not apply fixes; offer them as the next task.
