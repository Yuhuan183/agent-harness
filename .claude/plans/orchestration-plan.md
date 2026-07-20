# Orchestration and Monitoring — Current Plan

> 現況、未決項與必要決策紀錄。Runtime 規則以 `CLAUDE.md` 為準；使用方式以 `README.md` 與 `docs/` 為準；完整歷史由 Git 保存。

## Current architecture — 2026-07-17

| Surface | Current design | Evidence |
|---|---|---|
| CLI output | `rtk` PreToolUse rewrite, fail-open | `settings.json`, `RTK.md` |
| Context compression | Headroom wrap mode (recommended default) + optional persistent install; no durable proxy routing in tracked settings | `../.agents/docs/headroom-runtime.md` |
| Orchestration | Direct-first brake distilled from Baton `0ab4d2e` | `CLAUDE.md`, `skills/baton-dispatch/` |
| Roles | Seven self-contained leaf contracts; model owned by frontmatter; effort pinned or follows the main session (capped at high) | `agents/` |
| Verification | Focused checks first; Plan and outcome verifiers are capability-separated | `agents/plan-verifier.md`, `agents/verifier.md` |
| Monitoring | Delegation audit, weekly drift check, usage metadata report, runtime guard | `hooks/`, `scripts/` |
| Portability | Claude source of truth distilled into Codex and ChatGPT bundles after local review | `../.codex/`（本目錄） |

Main model and effort are user-selected. Reference H is Fable/low or Opus/high; X is Fable/medium or Opus/high. Role effort is two-tier: pinned low for mechanical roles (`Explore`, `mech-executor`); all thinking roles omit frontmatter effort and follow the main session, capped at high. Tracked settings define no main model or provider fallback.

## Verified mechanisms

- Delegation audit records start/stop, detects `spawnDepth >= 2`, and remains fail-open.
- Weekly integrity reports dirty contract state and delegation alarms; throttle advances only after both checks complete.
- Runtime guard blocks capability-sensitive reviewers below Claude Code 2.1.207 or when version is unknown.
- Usage report reads assistant usage metadata only, separates main/subagent/historical observer traffic, and calculates rolling-window peaks without claiming subscription-quota equivalence.
- Statusline parses payload once and resolves Git data against `workspace.current_dir`.
- Contract tests cover role ownership, main/leaf separation, routing, scope boundaries, hooks, Headroom, usage reporting, and platform bundle invariants.

## Current routing decisions

- Main orchestration is short and resident; leaf roles are self-contained and never read orchestration docs or spawn agents.
- `Explore` is the single broad-search role. The duplicate `scout` role was removed.
- `plan-verifier` and conditional `verifier` use Opus at the main session's effort. Security is GPT-primary at Sol/high, with a single Claude Opus fallback at the main session's effort.
- Provider fallback is one hop from the origin provider and never circular. Standalone Codex cannot dispatch Claude automatically; it reports the failure and requests manual handoff.
- High-complexity or materially uncertain provider choice uses the three-option user gate. Dual-provider implementation always has one writer.
- Finished agent responses are collected directly; follow-up runs must contain genuinely new or redirected work.
- Approved scope is a hard boundary; adjacent capabilities require a new main-session decision.

## Open observations

- Cross-provider live smoke is pending because the local Claude CLI is not authenticated. Static contracts are verified; runtime dispatch is not.
- Permission matching before/after `rtk` command rewrite still needs a focused live probe.
- OTel remains deferred. Revisit only if existing JSONL/transcript telemetry cannot answer a concrete routing question requiring real-time data.
- Codex App may rewrite machine `config.toml`; deployment must merge and recheck local state instead of replacing it.

## Decision log

- **2026-07-12** — Adopted fail-open local monitoring and nested-delegation detection.
- **2026-07-15** — Replaced fixed phase pipelines with direct-first, cost-aware dispatch; selected Headroom wrap ownership; removed routine stacked verification.
- **2026-07-17** — Added finished-task result collection and Baton approved-scope boundary; removed tracked main model/effort/fallback; adopted single-hop cross-provider routing and GPT-primary security.
- **2026-07-17** — Distilled runtime documentation: one authoritative location per concern, short main-only rules, self-contained leaf roles, and platform bundles updated only after Claude source stabilization.
- **2026-07-20** — Removed the `-xhigh` role variants; effort is capped at high and split into two tiers (pinned low for `Explore`/`mech-executor`; all thinking roles follow the main session's effort). Every dispatch (Claude role or Codex bridge) is reported to the user with task, provider, model, and effort; the main session quality-checks subagent output before integration. Added Codex counterparts for each leaf role, invocable from Claude via the codex-rescue bridge (role contract prepended to the brief) and natively as Codex custom agents; provider choice per role is steered by accumulated dispatch experience (`telemetry/delegation.jsonl` and session observations), not fixed rules.
- **2026-07-20** — Added the `experience-ledger` shared skill: per-dispatch outcome ledger (`~/.agents/telemetry/experience.jsonl`) with standardized role x provider metrics (AR/CR/RB/FR/QS) and an explore/prefer decision rule (n>=5, AR lead >=10pt); provider hints are directional, main session keeps final judgment.
- **2026-07-18** — Verified Headroom docs against upstream v0.32: `wrap` remains the recommended default (not deprecated); documented persistent `install` (launchd/systemd) as an optional always-on alternative. Reaffirmed base URL stays machine-local — never committed to tracked `settings.json`.

## Verification

Run before declaring the harness coherent:

```bash
python3 -m unittest discover -s tests -v
jq empty settings.json examples/headroom-mcp.merge.json
sh -n sh/statusline.sh
git diff --check
```

Live smoke after Claude authentication: direct known-target lookup; one broad `Explore`; high-complexity three-option gate; GPT-origin failure handoff; fallback-stop behavior; old-version runtime warning.
