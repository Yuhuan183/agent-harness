# Orchestration and Monitoring — Current Plan

> 現況、目標與決策紀錄。Runtime 規則以 `CLAUDE.md` 為準；使用方式以 `README.md` 與 `docs/` 為準；完整歷史由 Git 保存。

## Current architecture — 2026-07-22

| Surface | Current design | Evidence |
|---|---|---|
| CLI output | `rtk` PreToolUse rewrite, fail-open | `settings.json`, `RTK.md` |
| Context compression | Headroom wrap mode (recommended default) + optional persistent install; no durable proxy routing in tracked settings | `../.agents/docs/headroom-runtime.md` |
| Orchestration | Direct-first brake distilled from Baton `0ab4d2e` | `CLAUDE.md`, `skills/baton-dispatch/` |
| Roles | Seven self-contained leaf contracts; model and effort owned by frontmatter | `agents/` |
| Routing data | Per-provider routing files with quality floors and priority profiles | `model-routing.toml`, `../.codex/model-routing.toml` |
| Verification | Focused checks first; Plan and outcome verifiers are capability-separated | `agents/plan-verifier.md`, `agents/verifier.md` |
| Monitoring | Delegation audit, weekly drift check, usage metadata report, runtime guard | `hooks/`, `scripts/` |
| Portability | Claude source of truth distilled into Codex and ChatGPT bundles after local review | `../.codex/` |

## Routing policy (summary)

- **Main session**: model and effort are user-selected; tracked settings pin neither. Reference profiles: H = Fable/low or Opus/high; X = Fable at medium–xhigh or Opus/high (xhigh is main-session-only).
- **Role tiers**: pinned — `Explore` haiku/low, `mech-executor` sonnet/low, `executor` sonnet/medium, `plan-verifier` opus/high; follow — `verifier`, `security-reviewer`, `security-executor` inherit main-session effort, capped at high.
- **Codex bridge**: every leaf dispatch resolves model/effort via `~/.codex/scripts/model-routing` (single source of truth); Sol and Luna bridge overrides are smoke-tested (2026-07-22, rollout-verified).
- **Cross-provider**: single-hop fallback from the task's origin, never circular; security is GPT-primary at Sol/high with one Claude Opus fallback; dual-provider implementation always has one writer. High-complexity or uncertain provider choice uses the three-option user gate.
- **Experience loop**: every dispatch is reported (`dispatch: <task> — <role>@<provider> <model>/<effort>`), quality-checked, and logged to the experience ledger (AR/CR/RB/FR/QS; explore until n>=5 per provider, prefer at decayed Beta P(win)>=0.85). Hints are directional; main session keeps final judgment.
- **Scope**: leaf roles never orchestrate or read orchestration docs; approved scope is a hard boundary; follow-up runs must contain genuinely new work.

## Verified mechanisms

- Delegation audit records start/stop, detects `spawnDepth >= 2`, and remains fail-open.
- Weekly integrity reports dirty contract state, delegation alarms, and an empty-ledger warning.
- Runtime guard blocks capability-sensitive reviewers below Claude Code 2.1.207 or when version is unknown.
- Usage report separates main/subagent/historical traffic without claiming subscription-quota equivalence; Codex tokens/quota come from local rollouts (`codex-usage`).
- Claude→Codex bridge verified end-to-end: resolver JSON → `codex:codex-rescue` dispatch → rollout telemetry confirms the model/effort override (Sol/low, Luna/low).
- Contract tests (42) cover role ownership, main/leaf separation, routing, scope boundaries, hooks, Headroom, usage reporting, and platform bundle invariants.

## Next goals

1. **完善 Claude 模型分派策略（比照 Codex 版本思路）**
   - Fill the experience ledger: log every dispatch outcome; reach n>=5 per role x provider cell.
   - Re-derive `.claude/model-routing.toml` profiles from ledger data per its `revision_policy` (AA aggregates stay priors only).
   - Consider a resolver-style consumer so the Claude routing file becomes operative rather than documentary.
2. **Provider 完善**
   - Extend bridge smoke coverage beyond explore (remaining roles and priorities); keep availability evidence dated and rollout-verified.
   - Quota-aware dispatch discipline: check `codex-usage --quota` before heavy Codex dispatch; prefer Claude roles when the window is tight.
   - Close remaining live probes: permission matching around `rtk` rewrite; GPT-origin failure handoff and fallback-stop behavior.

## Open items

- Experience ledger has zero reviewed outcomes; external benchmarks remain priors until sampled.
- OTel stays deferred unless JSONL/transcript telemetry cannot answer a concrete real-time routing question.
- Codex App may rewrite machine `config.toml`; deployment must merge and recheck local state instead of replacing it.

## Decision log

- **2026-07-12** — Fail-open local monitoring and nested-delegation detection.
- **2026-07-15** — Direct-first cost-aware dispatch replaced fixed pipelines; Headroom wrap ownership; no routine stacked verification.
- **2026-07-17** — Single-hop cross-provider routing, GPT-primary security, approved-scope boundary; removed tracked main model/effort/fallback. Distilled docs: one authoritative location per concern.
- **2026-07-18** — Headroom verified against upstream v0.32; base URL stays machine-local.
- **2026-07-20** — Two-tier role effort (capped at high); per-dispatch reporting and QC; Codex counterparts for each leaf role via the codex-rescue bridge. Added `experience-ledger` skill (AR/CR/RB/FR/QS, explore/prefer rule).
- **2026-07-21** — External rankings (AA v4.1, Coding Agent Index v1.2) demoted to priors; route on local acceptable-outcome cost. Experience schema v2 (tokens, review/rework, API cost).
- **2026-07-22** — X profile allows main-session xhigh. Added `.claude/model-routing.toml` (quality floors + profiles mirroring the Codex file; ledger-driven revision policy). Bridge smoke-tested end-to-end (Sol/low, Luna/low; Luna evidence upgraded). User-directed repins: `executor` sonnet/medium, `plan-verifier` opus/high.

## Verification

```bash
python3 -m unittest discover -s tests -v
jq empty settings.json examples/headroom-mcp.merge.json
sh -n sh/statusline.sh
git diff --check
```
