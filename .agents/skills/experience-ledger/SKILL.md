---
name: experience-ledger
description: Dispatch experience ledger and analysis — log each outcome after QC, accumulate role × provider metrics (AR/CR/RB/FR/QS), and steer data-driven provider choice. Trigger — logging a dispatch outcome (記錄派工結果), choosing a provider from experience (依經驗選 provider), inspecting metrics (看指標). Not for the dispatch decision itself (baton-dispatch), provider rules (provider-routing), or token usage analysis (usage-report).
---

# Experience Ledger

Turns "accumulated experience decides Claude or Codex" into an operating loop:
**dispatch → quality check → log → metrics → next choice**. The ledger lives at
`~/.agents/telemetry/experience.jsonl` (machine-local, never committed).

## Logging (one record per dispatch, after its quality check)

The SubagentStart/Stop hooks (`experience-pending.py`) stage role, wall-clock,
and session automatically; a native Claude dispatch then only needs its outcome:

```bash
~/.agents/skills/experience-ledger/scripts/experience-log \
  --from-pending --outcome accepted --class impl --task "auth refactor" --quality 4
```

- Explicit flags always override pending values. When completions overlap,
  `--from-pending` refuses to guess — pass the hook-generated `--dispatch-id`.
- **Route flags by request source.** Native Claude records may omit
  `--profile/--model/--effort`: the resolver fills them and tags the record
  `route_source: resolver-assumed` (pins are aliases; the resolver maps them to
  dated ids, so assumed routes never masquerade as verified evidence). Bridge
  stubs carry no route fields — pass all three explicitly (`bridge-brief`
  prints the exact post-QC command). Stub-less native Codex records need
  `--request-source codex` plus role, provider, and the full route.
- Log **every** dispatch — Claude roles and Codex bridge alike. Outcome is the
  main session's quality verdict: `accepted` (clean) / `corrected` (fixed
  before integration) / `rebriefed` (re-dispatched) / `failed` (dropped or
  fell back).
- Fallback hops record `--origin-provider`, `--parent-dispatch-id`, and
  `--fallback-hops`; the logger rejects hops > 1 (single-hop policy is
  enforced, not advisory).
- Hooks record `request_source` (`claude-code` / `claude-code-plugin-codex`),
  dispatch, rollout, input/output/cache tokens, and `secs` when available;
  native Codex uses `codex`. An ambiguous bridge rollout window is flagged and
  logged without tokens rather than misattributed. After QC add
  `--review-secs` / `--rework-secs`; add `--api-cost-usd` only from a reliable
  billing value.
- `--task` is a short neutral label — no secrets, no verbatim content;
  surprises go in `--note`.
- Use `--class recon` for locating/inventory work and `--class review` for
  adversarial repository review with a named lens (defaults to full QC). Never
  merge the two cohorts just because both ran on `Explore`.
- Deviating from a report hint requires a `--note` with the reason.

## Reporting (when provider choice is uncertain; weekly routine)

```bash
~/.agents/skills/experience-ledger/scripts/experience-report            # selection.default
~/.agents/skills/experience-ledger/scripts/experience-report --profile fast
```

Outputs role × task class × provider observed/decision n, AR/CR/RB/FR/QS,
sources, coverage, cost proxies, and hints. `--profile` evaluates hints against
that profile's routes on both providers; default is each side's
`selection.default`. Only schema-v3 production records with complete source and
route drive decisions; older data stays visible but cannot vote. Thresholds
come solely from the identical `revision_policy` in both `model-routing.toml`
files — currently 90-day window, 45-day half-life, n>=10 per cell,
P(win)>=0.90; the tools stop when the two sides disagree or fields are
missing. `smoke`/`other` never produce hints; costs compare only when both
sides have sufficient records in the same scope. **A hint is a direction, not
a verdict.**

Codex tokens and quota: `scripts/codex-usage` reads `token_count` events from
local `~/.codex/sessions/` rollouts. `--quota` shows account windows — check
before heavy dispatch; the short window (e.g. 5h) outranks the weekly one
because exhausting it stalls tasks immediately, so near its limit dispatch
Claude or wait for reset. Without flags it also prints recent session totals
and last-turn usage, usable as `--tokens-out` input.

Profile revision: `scripts/experience-revise` reads each side's
`revision_policy`, compares route cells only within the same role/task class
of the current deployment profile, filters candidates by quality floor **and
leaf-override availability**, and reports unsampled/insufficient/keep/consider.
It only suggests — role-wide changes remain a main-session decision across
cohorts.

Metric definitions, schema, honesty boundaries, and evolution cadence:
[references/metrics.md](references/metrics.md). Dispatch frequency and nesting
violations stay with `delegation-report`, which complements this ledger.
