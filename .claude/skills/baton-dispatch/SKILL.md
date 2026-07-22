---
name: baton-dispatch
description: Choose the dispatch shape — direct, one agent, bounded parallel, workflow, or isolated workspaces. Use for non-trivial fan-out, batches, or multiple writers. Do not use for small edits, known-target lookups, or tightly coupled debugging.
---

# Baton Dispatch

Apply the resident dispatch brake, then choose the smallest reliable shape. This is a local distillation of cablate/baton v0.1.1 plus scope fix `0ab4d2e`.

## Cost test (run before every dispatch)

A high-tier pinned agent (Opus/high) costs about as much as the main session — delegation saves no compute, and briefing, context reconstruction, collection, and quality-check are pure overhead in both tokens and wall-clock. Delegate only when at least one payoff clearly exceeds that overhead:

1. **Parallelism** — two or more genuinely independent workstreams where wall-clock matters.
2. **Context protection** — bulky reads or noisy output would pollute the main window that later judgment still needs.
3. **Fresh-context independence** — the value *is* the separate context (`verifier`, `plan-verifier`, `security-reviewer`).
4. **Cheaper tier** — a pinned low role (`Explore`, `mech-executor`) genuinely covers the task.

A single sequential task with none of these stays in main. When the payoff is marginal or uncertain, work directly — a wrong direct call costs one task; habitual marginal dispatch taxes every task.

## Routing guide

Keep small or tightly coupled work in main; use one `Explore` for broad discovery or one review lens, bounded parallel agents for independent surfaces, and isolated workspaces for competing writes. Repetition must prove one sample before batching, and `Workflow` still requires user opt-in. Never map request bullets directly to agents.

## Recurrence and batching

Do not use an item-count threshold to decide that repeated work should move out of main. Batch only when one stable one-shot brief completely states the goal, constraints, done criteria, ownership, and per-item acceptance, and every remaining item is independent and the same shape. Keep triage, exceptions, integration, and final acceptance in main; work that still depends on main's evolving evidence is not a batch.

An already-diagnosed review finding with a known root cause and remedy is execution work, not unknown-bug discovery. It may join other independent same-shape findings only when the stable-brief, ownership, acceptance, and cost tests all pass; delegation remains optional.

## Run design

1. Stabilize outcome, scope/non-scope, constraints, evidence, ledger task class, and scenario/lens.
2. Converge shared schemas, registries, config, generated output, and lockfiles.
3. Assign one owner to every writable artifact and name the integration owner.
4. Brief only minimum paths, local checks, output, and stop conditions.
5. Keep local checks local; run expensive or repository-wide gates after integration.
6. Preserve partial evidence when stopping or changing shape.

Keep the three routing dimensions separate: **role** defines authority and tools; **task class** forms the ledger cohort; **scenario/lens** focuses the brief without creating another role. Use `review` rather than `recon` for adversarial repository review. Do not change a model route merely because a new scenario label was added; collect comparable outcomes first.

The approved Plan or release slice is a hard boundary. Agents may report adjacent opportunities but must stop before adding a domain, table, API, service, deployment responsibility, or materially larger file/schema surface.

## Gate placement and Plan convergence

Use focused tests, builds, and static checks as intermediate evidence while iterating. When an independent outcome verifier is warranted, dispatch it at the smallest coherent integration boundary where the complete acceptance claim can be refuted; do not re-verify every small fix. Verify earlier when a change crosses security, cross-language or FFI, serialization or pre-aggregation, irreversible-operation, or integration-blocking boundaries.

Do not resubmit a substantially unchanged Plan to `plan-verifier`. Another readiness pass requires a material revision or new evidence. If disagreement remains unresolved, simplify the Plan, surface the blocker to the user, or defer the blocked scope; main must not silently overrule the verifier.

## Result collection

A finished agent's final response is its deliverable — the harness returns it on completion. Collect it from the finished task; never relaunch or ask a read-only recon agent (`Explore`, `plan-verifier`, `security-reviewer`) to relay, restate, or report back a result it already produced. Use the resume channel only for genuinely new or redirected work. Treat a single load-bearing recon fact as an unverified input: sanity-check or re-run it in main, since the `verifier` gate covers executor output, not reconnaissance.

Report the launch and the post-QC outcome as separate `LEAF_DISPATCH` and `LEAF_RESULT` records. The task label, role, task class, and route must match the experience-ledger entry; never bury either record inside prose.
Read [references/briefs-and-stops.md](references/briefs-and-stops.md) only when writing a brief, ownership map, or batch stop rule.
