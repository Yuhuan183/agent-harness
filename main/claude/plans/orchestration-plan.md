# Orchestration current state

> Current as of 2026-08-13. Completed migrations and superseded decisions live in
> [orchestration-history.md](orchestration-history.md); this file contains only the active contract.

## Direction

The main task owns framing, architecture, ambiguity, integration, synthesis, provider choice, and final judgment. Direct execution is the default. Dispatch is justified only by parallelism, context protection, or fresh-context independence.

Provider routing and dispatch mechanics are separate:

- `provider-routing` chooses provider, role, profile, fallback, and verifier eligibility.
- `baton-dispatch` owns dispatch shape, briefs, stops, fixed records, QC, and ledger handoff.
- `experience-ledger` records provider, request source, route, outcome, cost coverage, and review/rework.

## Active invariants

1. One owner per writable artifact; diagnosis, first fix, and live verification for one unknown bug stay in one reasoning chain.
2. Leaf agents never delegate. `leaf-redispatch` enforces the Claude boundary; Codex uses `agents.max_depth = 1`.
3. At most one outcome verifier is placed at the smallest coherent integration boundary.
4. Claude no-write roles have no Bash. Command-required independent verification uses a Codex `verifier` with `sandbox_mode = "read-only"`.
5. Security analysis is read-only until an approved contract exists; implementation then has one security executor.
6. A Plan gets at most two automatic material revisions for the same readiness-unit ID before options are surfaced to the user.
7. Fixed `[LEAF_DISPATCH]` and `[LEAF_RESULT]` records carry task identity, provider route, `request_source`, QC result, and the matching ledger identity.

## Provider and profile vocabulary

- Priorities: `balanced` (default), `fast`, `quality-guarded`.
- Claude named roles own model and effort in frontmatter.
- Codex named roles resolve model and reasoning effort from `model-routing.toml`.
- Cross-provider fallback is one hop to the matching role.
- `request_source` values are `claude-code`, `codex`, `claude-code-plugin-codex`, and `codex-claude-cli`.

Profile names are routing intent, not model names. Model aliases are verified from actual leaf transcripts; they are not inferred from vendor marketing labels.

## Enforcement inventory

The current fail-closed gates are:

- `commit-test-gate.py` (Bash 側) 與 `githooks/pre-commit` (git argv 側)
- `leaf-redispatch.py`
- `runtime-guard.py --gate`
- `verifier-quota.py`

Diagnostic hooks remain fail-open. Artifact ownership and semantic brief quality remain main-task judgments and are checked during QC rather than presented as shell-enforced guarantees.

## Verification commands

Use Python 3.11+:

```sh
main/.agents/scripts/python3-run -m unittest discover -s main/claude/tests -v
main/claude/scripts/model-routing validate
main/codex/scripts/model-routing validate
main/claude/scripts/model-routing check-pins
main/claude/scripts/model-routing check-aliases
main/.agents/scripts/python3-run scripts/prompt-surface-census.py --check docs/research/prompt-surface-census.json
scripts/sync.sh
```

`scripts/sync.sh` is a dry-run unless `--apply` is explicitly supplied. It performs preflight and parity checks but does not create backups.

## Remaining evidence gaps

- Pilotfish-derived controls are statically enforced by contracts and tests. Lifecycle replay is no longer unmeasured — `evals/replay/` ran 15 pre-registered runs on 2026-08-12 — but one batch settles little: interruption and conflicting leaf results showed no failure at 5 of 5, with an exact 95% lower bound of 0.478, and repeated correction lapsed on the contract's own `DECISION:` obligation in 10 of 25 turns. Read the intervals, not the percentages.
- Provider/model efficiency decisions stay exploratory until same-role, same-task-class route cells reach the configured sample floor.
- Headroom behavior must be reported separately as repository policy, installed package version, GitHub release tag, and live service state.

## Source map

- [provider-routing](../skills/provider-routing/SKILL.md)
- [baton-dispatch](../skills/baton-dispatch/SKILL.md)
- [experience-ledger](../../.agents/skills/experience-ledger/SKILL.md)
- [dispatch lifecycle](../../../docs/dispatch-lifecycle.md)
- [hook system](../../../docs/hook-system.md)
- [research synthesis](../../../docs/research/README.md)
