---
name: baton-dispatch
description: Choose direct work, one agent, bounded parallel agents, a user-authorized workflow, or isolated workspaces. Use for non-trivial fan-out, batches, migrations, or multiple writers. Do not use for small edits, known-target lookups, ordinary questions, or tightly coupled debugging.
---

# Baton Dispatch

Apply the resident dispatch brake, then choose the smallest reliable shape. This is a local distillation of cablate/baton v0.1.1 plus scope fix `0ab4d2e`.

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

Read [references/briefs-and-stops.md](references/briefs-and-stops.md) only when writing a brief, ownership map, or batch stop rule.
