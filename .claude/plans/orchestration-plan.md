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
- **Role pins**: every role pins model and effort from the active profile (no follow-tier). Balanced: `Explore` sonnet/low, `mech-executor` sonnet/medium, `executor` sonnet/high, `plan-verifier` opus/medium, `verifier`/`security-*` opus/high. Full matrix in `model-routing.toml`; profiles are user-directed priors maintained from ledger and benchmark data.
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
- Claude routing file is operative: `.claude/scripts/model-routing` validates the TOML, resolves role routes, and `check-pins` cross-checks agent frontmatter (also run weekly by the integrity hook, fail-open when the resolver is absent).
- Experience-ledger pipeline verified end-to-end on a real bridge dispatch: hook-staged stub → `--from-pending` → tokens/secs auto-captured from rollout delta.
- Quota discipline is short-window-first: `codex-usage --quota` lists the shorter window (e.g. 5h) before the weekly one and warns to hold Codex dispatch when it nears exhaustion.
- Contract tests (46) cover role ownership, main/leaf separation, routing, scope boundaries, hooks, Headroom, usage reporting, and platform bundle invariants.

## Next goals

> 分類規則：**for all** = 跨 provider 的機制與紀律;**for claude** = 只動 `.claude/` 契約、roles、routing;**for codex** = 只動 `.codex/` 契約、bridge、rollout 佐證。

### For all

- Fill the experience ledger: log every dispatch outcome after QC; reach n>=5 per role x provider cell (sampling live since 2026-07-22).
- Quota-aware dispatch discipline: check `codex-usage --quota` before heavy Codex dispatch. The short window (5h) outranks the weekly window — exhausting it stalls tasks immediately; near its limit, dispatch Claude or wait for reset regardless of weekly headroom.

### For Claude

- Re-derive `.claude/model-routing.toml` profiles from ledger data per its `revision_policy` (AA aggregates stay priors only).
- Live probe: permission matching around the `rtk` PreToolUse rewrite.

### For Codex

- Extend bridge smoke coverage to remaining roles and priorities as real dispatches occur (no dedicated quota burn); keep availability evidence dated and rollout-verified.
- Live probe: GPT-origin failure handoff and fallback-stop behavior.

## Open items

- **All**: OTel stays deferred unless JSONL/transcript telemetry cannot answer a concrete real-time routing question.
- **Codex**: Codex App may rewrite machine `config.toml`; deployment must merge and recheck local state instead of replacing it.

## Decision log

- **2026-07-12** — Fail-open local monitoring and nested-delegation detection.
- **2026-07-15** — Direct-first cost-aware dispatch replaced fixed pipelines; Headroom wrap ownership; no routine stacked verification.
- **2026-07-17** — Single-hop cross-provider routing, GPT-primary security, approved-scope boundary; removed tracked main model/effort/fallback. Distilled docs: one authoritative location per concern.
- **2026-07-18** — Headroom verified against upstream v0.32; base URL stays machine-local.
- **2026-07-20** — Two-tier role effort (capped at high); per-dispatch reporting and QC; Codex counterparts for each leaf role via the codex-rescue bridge. Added `experience-ledger` skill (AR/CR/RB/FR/QS, explore/prefer rule).
- **2026-07-21** — External rankings (AA v4.1, Coding Agent Index v1.2) demoted to priors; route on local acceptable-outcome cost. Experience schema v2 (tokens, review/rework, API cost).
- **2026-07-22** — X profile allows main-session xhigh. Claude routing made operative: `.claude/model-routing.toml` + resolver (validate/resolve/check-pins) wired into weekly integrity; resolver core shared in `.agents/scripts/routing_core.py`. Bridge smoke-tested end-to-end (Sol/low incl. mech-executor, Luna/low; rollout-verified); first ledger record logged. User-directed: follow-tier abolished — all roles pin effort from the profile matrix (see `model-routing.toml`; Haiku unrouted; critical admits opus/medium for verifier only); plan goals categorized (all/claude/codex); 5h short quota window overrides the weekly one. Token-overhead pass: descriptions trimmed, matrix prose deduplicated, contract source renamed `CLAUDE.contract.md` (no in-repo double load); added `bridge-brief`, `smoke` class, backup rotation.

## Verification

```bash
python3 -m unittest discover -s tests -v
jq empty settings.json examples/headroom-mcp.merge.json
sh -n sh/statusline.sh
git diff --check
```
