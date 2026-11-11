# Standardized Metrics Model

## Schema v3 (`~/.agents/telemetry/experience.jsonl`, one record per dispatch; compatible with v1/v2)

| Field | Required | Domain | Description |
|---|---|---|---|
| `ts` | ✓ | ISO 8601 UTC | Timestamp of ledger write (when quality-check completes) |
| `role` | ✓ | one of the seven leaf role names | Dispatched role |
| `provider` | ✓ | `claude` \| `codex` | Provider that actually executed |
| `request_source` | ✓ (v3) | `claude-code` \| `codex` \| `claude-code-plugin-codex` \| `codex-claude-cli` | Request origin and calling surface |
| `dispatch_id` / `rollout_id` | automatic (when available) | string | Ties outcome, hook, and provider telemetry to the same dispatch |
| `outcome` | ✓ | `accepted` \| `corrected` \| `rebriefed` \| `failed` | Main session's quality verdict |
| `profile` / `model` / `effort` | ✓ (production decision) | | Actual route; for Claude, backfilled from the active deployment preset |
| `tier` | | `spot` \| `full` | QC tier |
| `task_class` | ✓ | `recon` \| `review` \| `plan` \| `impl` \| `verify` \| `security` \| `smoke` \| `other` | Task type; `recon` is orientation/organization, `review` is adversarial project review with an explicit lens |
| `task` | | short neutral label | **must not contain secrets or verbatim content** |
| `quality` | | 1-5 | Subjective quality score (optional) |
| `tokens_in` / `tokens_out` | automatic (when available) | int | Standard input/output tokens |
| `cache_write_tokens` / `cache_read_tokens` | automatic (when available) | int | Cache-creation and cache-read tokens; all four categories must be present for a complete token count |
| `context_proxy` | automatic (from 2026-08-31) | `direct` \| `proxy:<service>/<version>` \| `proxy:unidentified` | Whether this session's model traffic crossed a compressing proxy, and which one. A cost reading taken through a compressor is not comparable to one taken direct. **A missing field means the row predates this and is unknown — never read it as `direct`**; that distinction is the whole point, because recording only the positive cases would make every old row look clean. Detected from the logging process's environment (`ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL`), which is the dispatching session's in the ordinary case; a cross-provider bridge is already visible through `origin_provider`. An endpoint that does not answer still yields `proxy:unidentified` rather than `direct` |
| `token_scope` | automatic | `full` \| `output_only` \| `partial` | Explicit cost-proxy scope; comparisons across scopes are prohibited |
| `telemetry_warning` | automatic (on anomaly) | string | e.g. multiple Codex rollouts landing in the same time window |
| `route_source` | automatic | `rollout-verified` \| `transcript-verified` \| `resolver-assumed` \| `explicit` | How well the route is attested, strongest first. `rollout-verified`: model and effort both matched Codex's applied thread settings. `transcript-verified`: the model Claude recorded on its own assistant turns matched the resolved pin (a dated snapshot of the same generation counts); Claude records no effort, so that half rests on `check-pins`. `resolver-assumed`: inferred by the resolver from an alias, and false the moment the alias is upgraded. `explicit`: passed by the dispatcher with nothing to check it against — a claim, not evidence. **Decision gate**: only the provider-attested tiers (`rollout-verified`, `transcript-verified`) may drive routing decisions; the rest are counted and shown as `ineligible_n` but never enter a cohort. `experience-report` and `experience-revise` share this rule through `core.DECISION_ROUTE_SOURCES`. A claimed route that contradicts the provider's record is refused at log time, not recorded |
| `origin_provider` / `parent_dispatch_id` / `fallback_hops` | on fallback | | Origin, failed dispatch, and hop count for a cross-provider fallback; the logger rejects hops > 1 |
| `secs` | should be recorded | float | **Execution-time proxy**: SubagentStart to SubagentStop; excludes subsequent main-session correction and integration |
| `review_secs` / `rework_secs` | optional, not aggregated | float | Main session's quality-check and correction/integration time. Still accepted so old rows stay editable; nothing is computed from them since 2026-09-30, when thirty days of recording left them at 3/181 and 0/181 |
| `api_cost_usd` | optional | float | Provider-verifiable actual API cost for this dispatch; leave blank for subscription plans |
| `note` | | short sentence | Noteworthy surprises worth remembering |

Outcome definitions:

- `accepted`: passed on the first try and went in as-is.
- `corrected`: the main session fixed it before integration.
- `rebriefed`: it needed a redispatch.
- `failed`: the main session discarded the output. Rows from before 2026-09-14 also use it for a provider fallback.

## Metrics (report output, grouped by role x task class x provider)

| Metric | Definition | How to read it |
|---|---|---|
| `n` | comparable sample size | n < 10 is always treated as insufficient evidence |
| `AR` | accepted / n | Primary metric: first-pass success rate |
| `CR` / `RB` / `FR` | share of corrected / rebriefed / failed | High RB = poor brief quality or wrong role choice; high FR = the route (model/effort) is not fit for the task |
| `QS` | average quality | Supplementary, subjective score |
| `avg_tokens_out` | mean output tokens | Compute-cost proxy; cannot be converted to USD without input/cache tokens and unit price |
| `avg_total_tokens` | mean of all four token categories combined | Only included when all four categories are present |
| `avg_secs` | mean subagent wall-clock time | **Execution-time proxy**: lower is better at the same AR; excludes main-session rework |
| `avg_api_cost_usd` | mean verifiable API cost | Compare only within the same pricing scope; not interchangeable with subscription allowances |

Coverage and averages ignore malformed legacy telemetry: negative values, non-finite floats, out-of-range quality scores, and Boolean values that pose as integers. The record stays visible in `observed_n`; the report excludes only the invalid metric.

One exception is a row that the reader cannot turn into a record at all. Examples are unparseable JSON, a non-object line, a wrongly typed keyed field, and a timezone-naive `ts`. Such a row has no cohort, so `observed_n` cannot hold it. The reports count these rows instead: `experience-report` and `experience-revise` both emit `unusable_rows` in JSON and a `warning:` line in text output. A non-zero count means that the ledger has damage, not that the window was quiet.

## Decision rules (ranking model/effort tiers)

1. **Time decay**: each record has the weight `0.5^(age_days / half_life)`, with a current half-life of 45 days. AR, CR, RB, FR, QS, and the averages are all weighted, so old evidence fades as models change. The tools read the window, sample size, half-life, and preference probability only from the routing file's `revision_policy`. A missing or invalid field stops the process.
2. Only schema-v3 production records with a valid `request_source`, `profile`, `model`, and `effort` count toward decisions. Legacy or incomplete records stay in `observed_n` and in source coverage, for diagnostics only. `smoke`/`other` must never produce a hint.
3. A hint ranks `model/effort` tiers inside one role × task-class cohort (with `--profile`, only that profile's rows). A tier takes part only when its own raw sample reaches `min_samples` (currently 10) and its route clears the profile's quality floor. The tools never pool samples from other profiles, models, or efforts to reach the threshold. With fewer than two such tiers, the result is **explore a second tier**.
4. With two or more, the tools compare the top two by AR. A Beta-posterior `P(win)` that reaches the configured threshold (currently 0.90) yields **prefer**; otherwise the result is **either**. The tools compare cost tie-breaks only when both tiers meet the sample threshold on the same field. Total and output tokens must never mix.
5. Rules produce a **hint, not a verdict**; when deviating from the hint, record the reason in `note`.

## Honesty boundaries

- **Counterfactual gap**: the ledger records only dispatches that happened. It has no control group for "what if main had done it directly". `delegation.jsonl` (`delegation-report`) covers dispatch frequency and nesting violations separately, without overlap.
- **Quality score is subjective**: QS is the main session's judgment and may drift over time. AR, RB, and FR come from behavior, so they are more stable.
- **Small samples and task conflation**: every role x task-class x provider cohort stays exploratory until it reaches the policy threshold. Even then, unpaired tasks still need the main session to judge differences in difficulty.
- **Scenario is not a new role**: role sets permissions, and task class sets the comparable cohort. The scenario or review lens stays only in the neutral `task` label or in the brief. Never merge `recon` and `review` under the same role for decisions.
- **Source is not an interchangeable sample**: the report shows the `request_sources` distribution. Rows from the retired Codex bundle ran under different context, queueing, and review conditions than `claude-code` rows on the same route. So source composition is a confounder even when the route matches. When it differs noticeably, do not treat aggregated cost as a clean comparison. Sample the same brief separately instead.
- **Time contains noise**: `secs` mixes in queueing, approval waits, and human delays; compare mean trends across providers, not single outliers.
- **Cost readings are not comparable across `context_proxy` values**: a compressing proxy rewrites the request, and a defective one can move the numbers far. One example is Headroom `#2085`. There, parallel subagents shared a fallback session id, so the frozen prefix churned and cache reads became cache writes. The issue reported about 4.4x cache-creation inflation. Rows with no `context_proxy` field predate 2026-08-31, and nobody can classify them. The 2026-08-28 trap batches crossed a proxy with that defect. Do not pool them with later rows. Do not read the missing field as evidence that they were clean.
- **Cost scope may be incomplete**: legacy records or some providers may lack input/cache tokens, API cost, or human time. The report shows the full proxy only when all fields exist. Subscription plans, latency value, and failure cost still need separate interpretation.
- The ledger is machine-local telemetry and **never enters the database**; the `task` and `note` fields must not contain secrets.
- The pending hook and the outcome logger serialize append and consume through the same lock. Overlapping completions still need `dispatch_id` for exact pairing. After validation, the logger cleans up the first complete stop stub that it reads, so a new completion in flight does not change the target. But the ledger append and the pending rewrite touch two separate files. So a crash between them can leave an already-logged stub behind; remove the duplicate by `dispatch_id` by hand. Cleanup keys on the dispatch id, not on `--from-pending`. A record logged entirely with explicit flags clears its stub too. Only a record logged without any dispatch id leaves a stub behind, and `weekly-integrity` reports it.
- `experience-report --json` separates the two kinds of hint: `hints` holds one line per cohort, and `hints_insufficient` names the cohorts whose line only says "collect more". Unattended consumers report the difference. A cohort exists for each role × task class, so an insufficient-data hint would never clear. An alarm that is always on trains the reader to skip the real one.

## Context-pressure diagnostics

Context pressure and account quota are separate signals:

- `codex-usage` reads the latest rollout `token_count` event and divides
  `last_token_usage.total_tokens` by `model_context_window`. The cumulative
  `total_token_usage` remains visible for cost diagnosis but is never used as
  current-window occupancy.
- Claude `usage-report` sums uncached input, cache creation, and cache read for
  each assistant turn, then reports P50/P95 by source/model and optionally by
  session. It does not add output tokens to the prompt-context proxy.
- The tools map windows by model family (opus, sonnet and fable at 1M), so a new
  generation keeps its family's window. Haiku and unknown ids use a
  conservative 200k fallback. Pass `--context-window` when you know the
  runtime's actual limit.

Both commands expose the same repository operations policy: `<30%` low,
`30–<50%` watch, `50–<65%` checkpoint, and `>=65%` compact or start a new
session before critical judgment. This is an intentionally early warning for
context rot and conflicting instructions, not a claim that any model fails at
a fixed percentage. Compare P95 trends and task outcomes before changing these
thresholds.

## Sampling a second rung on Claude

Native Claude records normally omit `--profile/--model/--effort`. The resolver
fills them from the role's frontmatter pin, and the transcript confirms the
model. A dispatch that overrode the pin through the Agent tool's `model`
argument breaks that assumption. The resolver still fills in the pin, the fill
contradicts the hook-recorded `observed_model`, and the logger refuses the
record as a routing violation. The error quotes a `--model` that the caller
never passed, which looks like a tooling bug until you know the shape. Pass the
model that actually ran. The tag stays `route_source: transcript-verified`.
An explicit value that agrees with the provider's own record is evidence, not a
hand-typed route, so these samples do enter their cohort.

The Agent tool overrides `model` only. Effort still comes from frontmatter, so a
dispatch samples the model axis of a role and never its effort ladder. For the
effort axis, or for any sample that must not touch deployed state, use
`evals/scripts/rung-run.py`. It runs the repo's contract in its own
`claude --print` process, with `--model` and `--effort` on the command line, so
no pin needs a restore afterwards. Those runs are sessions, not subagents. So no
hook stages a stub, and their records are `explicit`: they compare rungs, they
do not fill cohorts. Measured example: the 2026-08-06 `explore` rung comparison
in `evals/traps/s10-skill-recall/README.md`.

## Closing a dispatch nobody can still judge

`--cancel` retires a launch whose leaf never ran. You log anything that ran,
`failed` included. Neither covers a dispatch that ran and whose outcome went
unjudged until no reviewer is left. An invented outcome corrupts the cohort, and
a hand edit of the pending file removes the carrier that the weekly
reconciliation depends on. Close that case with

    experience-stage --abandon --dispatch-id <id> --reason "<why>"

which is deliberately a poor escape hatch:

- It refuses a dispatch under a day old, so nobody can use it to skip QC.
- It refuses a launch that never ran, and points at `--cancel`.
- It requires a reason, because an unexplained abandonment looks exactly like a
  forgotten one.
- It writes to `experience-abandoned.jsonl` beside the ledger, not into it, so
  no metric ever comes from a judgement that nobody made.

Precedent: on 2026-08-06, someone abandoned 23 stubs from a single 2026-07-27
session. They edited the pending file by hand, because this path did not exist
yet.

## Evolution cadence

Run `experience-report` weekly, together with the weekly-integrity cadence, and compare it against `delegation-report`. When a hint changes, update the preference note in `provider-routing`. For roles with persistently high RB, revisit the brief template or the cost-test criteria. `experience-revise` also uses only the route cells of the current deployment profile, so it does not mix the risk distributions of the fast and quality-guarded routes. Policy changes go only into the routing file's `revision_policy`, never into an ad hoc CLI override.
