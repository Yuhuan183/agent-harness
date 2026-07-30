---
name: experience-ledger
description: |
  Dispatch experience ledger and analysis — log each outcome after QC, accumulate role × provider metrics (AR/CR/RB/FR/QS), and steer data-driven provider choice.
  觸發：記錄派工結果、依經驗選 provider、看派工指標、"log this dispatch"、"which provider is winning"。
  不觸發：派工決策本身（baton-dispatch）、provider 規則（provider-routing）、token 用量分析（usage-report）。
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
  Any run that names a `--dispatch-id` clears that dispatch's staged stub, so a
  fully explicit record reconciles the pending file the same way.
- **Route flags by request source.** Omit `--profile/--model/--effort` on
  native Claude records: the model comes from the dispatch's own transcript and
  the rest from the resolver, tagged `route_source: transcript-verified`. Only
  provider-attested tiers may drive a route change, so typing the route in
  cannot make a record count — with no staged evidence the resolver's fill is
  tagged `resolver-assumed` and a hand-typed route is tagged `explicit`, and
  neither enters a cohort. Bridge records read model and effort from the
  dispatch's own Codex rollout and tag `route_source: rollout-verified`; pass
  only `--profile` (a harness label the provider does not record). A
  `--model/--effort` that contradicts the provider's record is rejected as a
  routing violation rather than logged. Native Codex records carry the full
  route explicitly; role, provider, and request source come from the staged
  launch below.
- **Native Codex stages its own carrier.** There is no dispatch hook there, so
  `scripts/experience-stage --start --role <role>` at launch prints the
  dispatch id for both fixed records, and `--stop` records the completion;
  `--cancel` retires a launch whose leaf never ran. Without a staged launch a
  forgotten outcome leaves no trace, and `weekly-integrity` reports staged
  dispatches the ledger never answered.
- Log **every** dispatch — Claude roles, Codex bridge, and native Codex alike.
  Outcome is the
  main session's quality verdict: `accepted` (clean) / `corrected` (fixed
  before integration) / `rebriefed` (re-dispatched) / `failed` (dropped or
  fell back).
- Fallback hops record `--origin-provider`, `--parent-dispatch-id`, and
  `--fallback-hops`; the logger rejects hops > 1 (single-hop policy is
  enforced, not advisory).
- Hooks record `request_source` (`claude-code` / `claude-code-plugin-codex`);
  native Codex uses `codex`, and Codex-launched Claude CLI uses `codex-claude-cli`.
  Hooks also record dispatch, rollout, input/output/cache tokens, and `secs`
  when available. An ambiguous bridge rollout window is flagged and
  logged without tokens rather than misattributed. After QC add
  `--review-secs` / `--rework-secs`; add `--api-cost-usd` only from a reliable
  billing value.
- `--task` is a short neutral label — no secrets, no verbatim content;
  surprises go in `--note`.
- Use `--class recon` for locating/inventory work and `--class review` for
  adversarial repository review with a named lens (defaults to full QC). Never
  merge the two cohorts just because both ran on `explore`.
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
and last-turn usage, usable as `--tokens-out` input. Its `attention` line uses
the runtime-reported **last-turn total / model context window**, not cumulative
session tokens or subscription quota. Treat 30% as watch, 50% as checkpoint,
and 65% as compact/new-session before critical judgment; these are repository
operations thresholds, not provider guarantees. Use `--json` for the exact
counter fields and policy.

Profile revision: `scripts/experience-revise` reads each side's
`revision_policy`, compares route cells only within the same role/task class
of the current deployment profile, filters candidates by quality floor **and
leaf-override availability**, and reports unsampled/insufficient/keep/consider.
It only suggests — role-wide changes remain a main-session decision across
cohorts.

Metric definitions, schema, honesty boundaries, and evolution cadence:
[references/metrics.md](references/metrics.md). Dispatch frequency and nesting
violations stay with `delegation-report`, which complements this ledger.
