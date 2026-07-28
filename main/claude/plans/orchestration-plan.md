# Orchestration and Monitoring — Current Plan

> 只保留當前最新方案。Runtime 規則以 `CLAUDE.md` 為準；使用方式以 `README.md` 與 `docs/` 為準；決策歷程見 [orchestration-history.md](orchestration-history.md)，完整差異由 Git 保存。

## Current architecture — 2026-07-22

| Surface | Current design | Evidence |
|---|---|---|
| CLI output | `rtk` PreToolUse rewrite, fail-open | `settings.json`, `RTK.md` |
| Context compression | Headroom wrap mode (recommended default) + optional persistent install; no durable proxy routing in tracked settings | `../../.agents/docs/headroom-runtime.md` |
| Orchestration | Direct-first brake from Baton `0ab4d2e`, plus Pilotfish v1.3 shape-based batching and Plan anti-churn | `CLAUDE.md`, `skills/baton-dispatch/` |
| Roles | Seven self-contained capability contracts; task class and scenario refine work without role proliferation | `agents/`, `skills/baton-dispatch/` |
| Routing data | Per-provider routing files with quality floors and priority profiles | `../model-routing.toml`, `../../.codex/model-routing.toml` |
| Verification | Plan/outcome roles stay capability-separated; fresh outcome verification uses the smallest coherent integration boundary | `agents/plan-verifier.md`, `agents/verifier.md` |
| Monitoring | Delegation audit, weekly drift check, usage metadata report, runtime guard | `hooks/`, `scripts/` |
| Portability | Claude source of truth distilled into Codex and ChatGPT bundles after local review | `../../.codex/` |

## Routing policy (summary)

- **Main session**: model and effort are user-selected; tracked settings pin neither. Reference profiles: H = Opus/high or Fable/low; X = Opus/high or Fable at medium–xhigh (xhigh is main-session-only); Opus leads both since 2026-07-25 measured data.
- **Role pins**: Claude profiles are deployment presets, not per-dispatch routes. Balanced pins `explore` sonnet/low, `mech-executor` sonnet/medium, `executor` opus/medium, `plan-verifier` opus/medium, and `verifier`/`security-*` opus/high. Pins name a tier alias and the CLI resolves the generation (`opus` → `claude-opus-5`), so a generation move edits the alias map and the routing table but never the seven agent files; `check-aliases` verifies the alias-to-generation claim against leaf transcripts. `activate-profile` updates all frontmatter pins and `selection.default` transactionally in source before sync.
- **Codex bridge**: every leaf dispatch resolves model/effort via `~/.codex/scripts/model-routing` (single source of truth); Sol and Luna bridge overrides are smoke-tested (2026-07-22, rollout-verified).
- **Cross-provider**: provider choice is CP-first (local reports + external priors + ledger; usage alarm switches to the provider with headroom, asking the user when material). Single-hop fallback from the task's origin, never circular; security routes like any role at its critical floor; dual-provider implementation always has one writer. Uncertain choice uses the three-option user gate.
- **Experience loop**: every dispatch uses separate `LEAF_DISPATCH` and post-QC `LEAF_RESULT` records, then logs the same neutral task label, task class, source (`claude-code`, `codex`, or `claude-code-plugin-codex`), and route. `recon` and adversarial `review` are separate cohorts. Policy is config-driven: 90d window, 45d half-life, n>=10 per role/task-class route cell, P(win)>=0.90; smoke/other and mismatched token scopes cannot drive preference.
- **Scope**: leaf roles never orchestrate or read orchestration docs; approved scope is a hard boundary; follow-up runs must contain genuinely new work.

## Verified mechanisms

- Delegation audit records start/stop, detects `spawnDepth >= 2`, and remains fail-open.
- `scripts/deployment-manifest.tsv` is the single source for sync and weekly drift coverage across Claude, Codex, and shared artifacts; weekly integrity also reports pin drift, delegation alarms, and an empty-ledger warning.
- Runtime guard warns at SessionStart and actually blocks restricted reviewer dispatch via a PreToolUse Agent gate (exit 2) below Claude Code 2.1.207 or when version is unknown; the version probe is cached by binary mtime.
- Usage report separates main/subagent/historical traffic without claiming subscription-quota equivalence; Codex tokens/quota come from local rollouts (`codex-usage`).
- Claude→Codex bridge verified end-to-end: resolver JSON → `codex:codex-rescue` dispatch → rollout telemetry confirms the model/effort override (Sol/low, Luna/low).
- Claude routing file is operative: `main/claude/scripts/model-routing` validates the TOML, resolves role routes, and `check-pins` cross-checks agent frontmatter (also run weekly by the integrity hook, fail-open when the resolver is absent).
- Experience schema v3 records dispatch/rollout identity and request source; ambiguous bridge rollout windows retain a warning instead of adding unrelated token totals.
- Quota discipline is short-window-first: `codex-usage --quota` lists the shorter window (e.g. 5h) before the weekly one and warns to hold Codex dispatch when it nears exhaustion.
- Contract tests are split by concern (roles/contracts/deployment/mechanisms/ledger) with word-based doc budgets and twin-role semantic parity checks; coverage spans role ownership, preset atomicity, routing, policy validation, ledger concurrency, deployment preflight, hooks, and platform bundles.

## Next goals

> 分類規則：**for all** = 跨 provider 的機制與紀律；**for claude** = 只動 `main/claude/` 契約、roles、routing；**for codex** = 只動 `main/codex/` 契約、bridge、rollout 佐證。

### For all

- Fill comparable cohorts: record every dispatch after QC, including source/profile/model/effort; reach n>=10 per role × task class × route cell before route preference.
- Quota-aware dispatch discipline: check `codex-usage --quota` before heavy Codex dispatch. The short window (5h) outranks the weekly window — exhausting it stalls tasks immediately; near its limit, dispatch Claude or wait for reset regardless of weekly headroom.

### For Claude

- Review `experience-revise` suggestions only after policy thresholds are met; apply a Claude role-wide change through a source deployment preset, never from one mixed cohort.
- F-06 follow-up: Claude pins are aliases, so ledger routes stay `route_source: resolver-assumed`. **Precondition now met (2026-07-25)** — `model-routing check-aliases` reads the real `message.model` from leaf transcripts, so the runtime id is available to compare against the assumed route. Remaining work: have `experience-log` record `transcript-verified` when the observed id matches, and keep pre-upgrade assumed records from being credited to the new generation.
- Live probe: permission matching around the `rtk` PreToolUse rewrite.

### For Codex

- Extend bridge smoke coverage to remaining roles and priorities as real dispatches occur (no dedicated quota burn); keep availability evidence dated and rollout-verified.
- Live probe: GPT-origin failure handoff and fallback-stop behavior.

## Remediation plan — 2026-07-26 dual-provider review (landed)

Waves 1–4 landed across the 2026-07-26/27 sessions: the Claude read-only Bash
boundary (`readonly-bash.py` + `test_contracts.py:296` parity), managed-entry
permission retraction, gate-line anchoring, and the cardinality/ownership
carriers (bridge `dispatch_id`, `verifier-quota`). Wave 5–6 doc items landed
too. The second-pass review below re-verified the security-relevant ones and
closed the remaining `config.merge.toml` and language-rule items.

## Second-pass review — 2026-07-27

Each finding was spot-verified before acting; the reproducible ones were fixed,
the rest recorded as audited-not-a-defect so they are not re-opened blindly.

- **Fixed (reproduced first):** `readonly-bash` chained-command/newline bypass
  (`shlex.split` glued `.;rm`/`.&&rm` and swallowed a post-newline head — a
  segment-aware tokenizer now validates each segment, and `>&file`/`&>file` are
  closed); `commit-test-gate` backslash-newline continuation slipping the
  `git … commit` prefilter; `weekly-integrity` outer SessionStart timeout (15 s)
  shorter than its slowest inner subprocess (rsync 30 s), which killed
  drift-heavy runs before the throttle stamp — now 60 s (`outer > max(inner)`);
  the `config.merge.toml` "manual merge" wording (`sync.sh` `merge-toml` applies
  it); and the language rule's narrow trigger-metadata / template exception.
- **Audited, no fix:** `route_source` does not gate `decision_eligible` by
  design (the whole Claude side is `resolver-assumed`); `verifier-quota`'s
  `prompt_id` scope and read-modify-write are a documented budget marker, not a
  safety boundary; `quality_floor` is documented in-code as a curated list, not
  a magnitude threshold; the git-managed-`~/.claude` drift path relies on that
  repo's own `git status`, a rare-deployment gap left as a note.

## Open items

- **All**: OTel stays deferred unless JSONL/transcript telemetry cannot answer a concrete real-time routing question.
- **Codex**: Codex App may rewrite machine `config.toml`; deployment must merge and recheck local state instead of replacing it.
- **Fable fallback avoidance**: four unimplemented directions recorded in [fable-5-fallback](../../../docs/fable-5-fallback.md) (heuristic dispatch-hint hook, payoff codification, routing disambiguation, main-session model audit) — approach and principle noted, decision deferred.
- **Punctuation sweep**: rule stated ([docs/README.md](../../../docs/README.md) rule 7); converting the ~1695 remaining full-width marks is approved but low priority (2026-07-28) — convert per edited paragraph, never repo-wide.

## Decision history

完整依時間序的決策紀錄在 [orchestration-history.md](orchestration-history.md)（append-only）；本檔只保留當前方案。

## Verification

```bash
python3 -m unittest discover -s tests -v
jq empty settings.json examples/headroom-mcp.merge.json
sh -n sh/statusline.sh
git diff --check
```
