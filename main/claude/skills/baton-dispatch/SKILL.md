---
name: baton-dispatch
description: |
  Decide the dispatch shape — direct, one agent, bounded parallel, workflow, or isolated workspaces. Load once a dispatch is going ahead; it owns briefs, ownership, batching, collection, QC, and the fixed record formats.
  觸發：已經決定要派工、「怎麼拆」「平行處理」「批次」「多個 writer」。
  不觸發：小修改、已知目標查找、緊耦合除錯（留在 main 直接做）。
---

# Baton Dispatch

Apply the resident dispatch brake, then choose the smallest reliable shape. This skill owns dispatch shape, grouping, briefs, collection, QC, and fixed records. It does not choose a provider/model or decide verifier eligibility; load `provider-routing` for those decisions. This is a local distillation of cablate/baton v0.1.1 plus scope fix `0ab4d2e`.

## Cost test

A high-tier pinned agent (Opus/high) costs about as much as the main session — delegation saves no compute, and briefing, context reconstruction, collection, and quality-check are pure overhead in both tokens and wall-clock. Delegate only when at least one payoff clearly exceeds that overhead:

1. **Parallelism** — two or more genuinely independent workstreams where wall-clock matters.
2. **Context protection** — bulky reads or noisy output would pollute the main window that later judgment still needs.
3. **Fresh-context independence** — the value *is* the separate context (`verifier`, `plan-verifier`, `security-reviewer`).
4. **Cheaper tier** — a pinned low role (`explore`, `mech-executor`) genuinely covers the task.

A single sequential task with none of these stays in main. When the payoff is marginal or uncertain, work directly — a wrong direct call costs one task; habitual marginal dispatch taxes every task.

## Dispatch shape

Keep small or tightly coupled work in main; use one `explore` for broad discovery or one review lens, bounded parallel agents for independent surfaces, and isolated workspaces for competing writes. Repetition must prove one sample before batching, and `Workflow` still requires user opt-in. Never map request bullets directly to agents.

## Recurrence and batching

Do not use an item-count threshold to decide that repeated work should move out of main. Batch only when one stable one-shot brief completely states the goal, constraints, done criteria, ownership, and per-item acceptance, and every remaining item is independent and the same shape. Keep triage, exceptions, integration, and final acceptance in main; work that still depends on main's evolving evidence is not a batch.

An already-diagnosed review finding with a known root cause and remedy is execution work, not unknown-bug discovery. It may join other independent same-shape findings only when the stable-brief, ownership, acceptance, and cost tests all pass; delegation remains optional.

## Run design

1. Stabilize outcome, scope/non-scope, constraints, evidence, ledger task class, and scenario/lens.
2. Converge shared schemas, registries, config, generated output, and lockfiles.
3. Assign one owner to every writable artifact, name the integration owner, and map read scopes for parallel discovery.
4. Brief only minimum paths, local checks, output, and stop conditions.
5. Keep local checks local; run expensive or repository-wide gates after integration.

An active agent-owned read scope is temporarily exclusive: main must not read or analyze it until collection unless it first cancels or redirects that agent. Launch every selected agent in one independent batch back-to-back, collect all required results, then begin cross-surface synthesis.

Keep the three routing dimensions separate: **role** defines authority and tools; **task class** forms the ledger cohort; **scenario/lens** focuses the brief without creating another role. Use `review` rather than `recon` for adversarial repository review. Do not change a model route merely because a new scenario label was added; collect comparable outcomes first.

The approved Plan or release slice is a hard boundary. Agents may report adjacent opportunities but must stop before adding a domain, table, API, service, deployment responsibility, or materially larger file/schema surface.

Claude no-write roles cannot execute Bash. Command-required independent verification belongs to a Codex `verifier` with `sandbox_mode = "read-only"`.

## Gate placement and Plan convergence

Use focused tests, builds, and static checks as intermediate evidence while iterating. `provider-routing` owns verifier eligibility; this skill owns placement. Place a triggered verifier at the smallest coherent integration boundary where the complete acceptance claim can be refuted; do not re-verify every small fix.

Cap a target at five verification passes. The cap does not widen the one-verifier quota: that quota is one outcome verifier per acceptance claim, and only a changed candidate is a new claim — so the passes are single verifiers in succession, and an unchanged candidate is not re-verified at all. Every pass after the first names what changed since the previous one. At the cap, stop and surface the open findings instead of dispatching again.

For large work, define a program envelope for shared constraints and independently approvable execution slices. Give each readiness unit a stable ID; each slice names its ready envelope, prerequisites, owner, rollback, and acceptance. Review the envelope first, then only the next executable slice. Unrelated downstream slices do not block approval; shared blockers cannot be hidden by cosmetic splitting.

Before the first readiness review of a security-sensitive unit, complete `security-reviewer` and carry every finding plus its disposition into the Plan. Ask `plan-verifier` for bare `READY` or `REVISE` blocks with `Blocker`, `Evidence`, `Minimum revision`, and `Acceptance check`. Materially revise after `REVISE`; after two automatic revisions of the same readiness-unit ID, stop and surface options. Never resubmit a substantially unchanged Plan without material revision or new evidence; simplify, surface, or defer unresolved scope rather than silently overrule the verifier.

## Result collection


```text
[LEAF_DISPATCH] dispatch_id=<id>|task=<label>|role=<role>|class=<class>|request_source=<request_source>|route=<profile>/<provider>/<model>/<effort>|reason=<payoff>
[LEAF_RESULT] dispatch_id=<id>|task=<label>|outcome=<accepted|corrected|rebriefed|failed>|qc=<spot|full>|ledger=<logged|skipped(reason)>
```

A finished agent's final response is its deliverable — the harness returns it on completion. Collect it from the finished task; never relaunch or ask a read-only recon agent (`explore`, `plan-verifier`, `security-reviewer`) to relay, restate, or report back a result it already produced. Use the resume channel only for genuinely new or redirected work. Treat a single load-bearing recon fact as an unverified input: sanity-check or re-run it in main, since the `verifier` gate covers executor output, not reconnaissance.

Report the launch and the post-QC outcome as separate fixed records, never buried in prose, in exactly the two shapes above — `dispatch_id` included, since it is what ties the record to the pending stub and the ledger. Use actual active/resolved route values; native roles use request_source `claude-code`, bridge roles `claude-code-plugin-codex`. After QC, load `experience-ledger` and log the same neutral task label, task class, route, request source, and outcome; never claim `logged` before the command succeeds.

Use spot QC for mechanical work from a complete spec; use full QC for judgment-heavy or verification work. Both tiers hunt false-completion frauds: weakened or bypassed checks, fixtures fabricated to satisfy a check, undeclared out-of-scope changes, missing owed `INTENT:`/`TWINS:`/`AUTH:` lines, and leftover leaf-created scratch files (pre-existing dirty-worktree files are not debris). Audit owed lines with `~/.claude/scripts/qc-gate-lines <report> --diff <diff-file> [--defect-fixed] [--outward-taken]`, setting flags from the diff and evidence, never from the report's claims. Never accept a `found 0/none` TWINS claim on the report's word: re-run the search yourself — grep the fixed construct across the scope — before accepting (`qc-gate-lines` flags these claims).
Read [references/briefs-and-stops.md](references/briefs-and-stops.md) only when writing a brief, ownership map, or batch stop rule.
