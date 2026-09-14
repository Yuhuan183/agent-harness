---
name: experience-ledger
description: |
  Dispatch experience ledger and analysis — log each outcome after QC, accumulate role × task-class metrics (AR/CR/RB/FR/QS), and steer data-driven route choice.
  觸發：記錄派工結果、依經驗選 model/effort、看派工指標、"log this dispatch"、"which route is winning"。
  不觸發：派工決策本身（baton-dispatch）、路由規則（provider-routing）、token 用量分析（usage-report）。
---

# Experience Ledger

Turns accumulated dispatch experience into an operating loop:
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
- **One record per dispatch, and none while its staged launch is open — both
  enforced, not intended.** A second log for an id already in the ledger is
  refused; that refusal still clears any staged stub, which is how a retry
  after a failed cleanup ends. A log for an id whose staged launch has no
  recorded completion is refused too: its outcome is not knowable yet, and
  writing one seals the id against the real one. That guard reads the pending
  file, so a never-staged id still logs — ordering is a dispatcher contract
  wherever no carrier exists. To correct a wrong outcome, edit the ledger: the
  metrics count rows, so a second row is another sample, not a fix.
- **Route flags are not yours to type.** Omit `--profile/--model/--effort`:
  the model comes from the dispatch's own transcript and the rest from the
  resolver, tagged `route_source: transcript-verified`. Only provider-attested
  tiers may drive a route change, so typing the route in cannot make a record
  count — with no staged evidence the resolver's fill is tagged
  `resolver-assumed` and a hand-typed route is tagged `explicit`, and neither
  enters a cohort. A `--model/--effort` contradicting the provider's record is
  rejected as a routing violation rather than logged.
- Log **every** dispatch. Outcome is the main session's quality verdict:
  `accepted` (clean) / `corrected` (fixed before integration) / `rebriefed`
  (re-dispatched) / `failed` (dropped or fell back). `weekly-integrity`
  reports staged dispatches the ledger never answered.
- Hooks record `request_source` (`claude-code`), dispatch id, input/output/
  cache tokens, and `secs` when available. After QC add `--review-secs` /
  `--rework-secs`; add `--api-cost-usd` only from a reliable billing value.
  The hop fields (`--origin-provider`, `--parent-dispatch-id`,
  `--fallback-hops`) stay enforced — the logger rejects hops > 1 — though no
  live route produces one.
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
sources, coverage, cost proxies, and hints. Hints rank `model/effort` tiers
inside one cohort; `--profile` evaluates them against that profile's routes,
defaulting to `selection.default`. Only schema-v3 production records with
complete source and route drive decisions; older data stays visible but cannot
vote. Thresholds come from `revision_policy` in `model-routing.toml` — 90-day
window, 45-day half-life, n>=10 per cell, P(win)>=0.90; the tools stop when
fields are missing. `smoke`/`other` never produce hints; costs compare only
when both tiers have sufficient records in the same scope. **A hint is a
direction, not a verdict.**

Profile revision: `scripts/experience-revise` reads `revision_policy`,
compares route cells only within the same role/task class
of the current deployment profile, filters candidates by quality floor **and
leaf-override availability**, and reports unsampled/insufficient/keep/consider.
It only suggests — role-wide changes remain a main-session decision across
cohorts.

Metric definitions, schema, honesty boundaries, and evolution cadence:
[references/metrics.md](references/metrics.md). Dispatch frequency and nesting
violations stay with `delegation-report`, which complements this ledger.
