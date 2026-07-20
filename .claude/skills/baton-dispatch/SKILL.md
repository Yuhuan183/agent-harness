---
name: baton-dispatch
description: Choose direct work, one agent, bounded parallel agents, a user-authorized workflow, or isolated workspaces. Use for non-trivial fan-out, batches, migrations, or multiple writers. Do not use for small edits, known-target lookups, ordinary questions, or tightly coupled debugging.
---

# Baton Dispatch

Apply the resident dispatch brake, then choose the smallest reliable shape. This is a local distillation of cablate/baton v0.1.1 plus scope fix `0ab4d2e`.

## Cost test (run before every dispatch)

A follow-tier agent runs at the main session's model and effort — delegation saves no compute, and briefing, context reconstruction, collection, and quality-check are pure overhead in both tokens and wall-clock. Delegate only when at least one payoff clearly exceeds that overhead:

1. **Parallelism** — two or more genuinely independent workstreams where wall-clock matters.
2. **Context protection** — bulky reads or noisy output would pollute the main window that later judgment still needs.
3. **Fresh-context independence** — the value *is* the separate context (`verifier`, `plan-verifier`, `security-reviewer`).
4. **Cheaper tier** — a pinned low role (`Explore`, `mech-executor`) genuinely covers the task.

A single sequential task with none of these stays in main. When the payoff is marginal or uncertain, work directly — a wrong direct call costs one task; habitual marginal dispatch taxes every task.

## Routing guide

| Shape | Use |
|---|---|
| Small or tightly coupled | Main session |
| Broad read-only discovery | One `Explore` run |
| Two to four independent surfaces | Bounded parallel agents |
| Repeated homogeneous items | Prove one sample, then batch; Workflow still requires user opt-in |
| Overlapping or competing writes | Isolated workspaces |
| Disjoint writes in shared state | Exclusive path owners plus central integration |

Never map request bullets directly to agents.

## Run design

1. Stabilize outcome, scope/non-scope, constraints, and evidence.
2. Converge shared schemas, registries, config, generated output, and lockfiles.
3. Assign one owner to every writable artifact and name the integration owner.
4. Brief only minimum paths, local checks, output, and stop conditions.
5. Keep local checks local; run expensive or repository-wide gates after integration.
6. Preserve partial evidence when stopping or changing shape.

The approved Plan or release slice is a hard boundary. Agents may report adjacent opportunities but must stop before adding a domain, table, API, service, deployment responsibility, or materially larger file/schema surface.

## Result collection

A finished agent's final response is its deliverable — the harness returns it on completion. Collect it from the finished task; never relaunch or ask a read-only recon agent (`Explore`, `plan-verifier`, `security-reviewer`) to relay, restate, or report back a result it already produced. Use the resume channel only for genuinely new or redirected work. Treat a single load-bearing recon fact as an unverified input: sanity-check or re-run it in main, since the `verifier` gate covers executor output, not reconnaissance.

Read [references/briefs-and-stops.md](references/briefs-and-stops.md) only when writing a brief, ownership map, or batch stop rule.
