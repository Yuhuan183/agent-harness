# Standardized Metrics Model

## Schema v3 (`~/.agents/telemetry/experience.jsonl`, one record per dispatch; compatible with v1/v2)

| Field | Required | Domain | Description |
|---|---|---|---|
| `ts` | ✓ | ISO 8601 UTC | Timestamp of ledger write (when quality-check completes) |
| `role` | ✓ | one of the seven leaf role names | Dispatched role |
| `provider` | ✓ | `claude` \| `codex` | Provider that actually executed |
| `request_source` | ✓ (v3) | `claude-code` \| `codex` \| `claude-code-plugin-codex` | Request origin and calling surface |
| `dispatch_id` / `rollout_id` | automatic (when available) | string | Ties outcome, hook, and provider telemetry to the same dispatch |
| `outcome` | ✓ | `accepted` \| `corrected` \| `rebriefed` \| `failed` | Main session's quality verdict |
| `profile` / `model` / `effort` | ✓ (production decision) | | Actual route; for Claude, backfilled from the active deployment preset |
| `tier` | | `spot` \| `full` | QC tier |
| `task_class` | ✓ | `recon` \| `review` \| `plan` \| `impl` \| `verify` \| `security` \| `smoke` \| `other` | Task type; `recon` is orientation/organization, `review` is adversarial project review with an explicit lens |
| `task` | | short neutral label | **must not contain secrets or verbatim content** |
| `quality` | | 1-5 | Subjective quality score (optional) |
| `tokens_in` / `tokens_out` | automatic (when available) | int | Standard input/output tokens |
| `cache_write_tokens` / `cache_read_tokens` | automatic (when available) | int | Cache-creation and cache-read tokens; all four categories must be present for a complete token count |
| `token_scope` | automatic | `full` \| `output_only` \| `partial` | Explicit cost-proxy scope; comparisons across scopes are prohibited |
| `telemetry_warning` | automatic (on anomaly) | string | e.g. multiple Codex rollouts landing in the same time window |
| `route_source` | automatic | `explicit` \| `resolver-assumed` | Whether the route field was passed explicitly or inferred by the resolver from an alias; inferred values must not be treated as verified evidence once the alias is upgraded |
| `origin_provider` / `parent_dispatch_id` / `fallback_hops` | on fallback | | Origin, failed dispatch, and hop count for a cross-provider fallback; the logger rejects hops > 1 |
| `secs` | should be recorded | float | **Execution-time proxy**: SubagentStart to SubagentStop; excludes subsequent main-session correction and integration |
| `review_secs` / `rework_secs` | should be recorded | float | Main session's quality-check and correction/integration time |
| `api_cost_usd` | optional | float | Provider-verifiable actual API cost for this dispatch; leave blank for subscription plans |
| `note` | | short sentence | Noteworthy surprises worth remembering |

Outcome definitions: `accepted` = passed on the first try, integrated as-is; `corrected` = main session fixed it before integrating; `rebriefed` = needed a redispatch; `failed` = output discarded or triggered a provider fallback.

## Metrics (report output, grouped by role x task class x provider)

| Metric | Definition | How to read it |
|---|---|---|
| `n` | comparable sample size | n < 10 is always treated as insufficient evidence |
| `AR` | accepted / n | Primary metric: first-pass success rate |
| `CR` / `RB` / `FR` | share of corrected / rebriefed / failed | High RB = poor brief quality or wrong role choice; high FR = provider not fit for the task |
| `QS` | average quality | Supplementary, subjective score |
| `avg_tokens_out` | mean output tokens | Compute-cost proxy; cannot be converted to USD without input/cache tokens and unit price |
| `avg_total_tokens` | mean of all four token categories combined | Only included when all four categories are present |
| `avg_secs` | mean subagent wall-clock time | **Execution-time proxy**: lower is better at the same AR; excludes main-session rework |
| `avg_total_secs` | mean of subagent + review + rework time | Included only when all three time fields are present; closer to end-to-end |
| `avg_api_cost_usd` | mean verifiable API cost | Compare only within the same pricing scope; not interchangeable with subscription allowances |

Coverage and averages ignore malformed legacy telemetry, including negative values, non-finite floats, out-of-range quality scores, and Boolean values masquerading as integers. The record remains visible in `observed_n`; only the invalid metric is excluded.

## Decision rules (standardized model for provider selection)

1. **Time decay**: each record is weighted `0.5^(age_days / half_life)` (current half-life: 45 days); AR/CR/RB/FR/QS/averages are all weighted values, so old evidence naturally fades as providers are upgraded. Window, sample size, half-life, and preference probability are read only from a `revision_policy` identical on both sides; a missing field or mismatched value halts the process.
2. Only schema-v3 production records with a valid `request_source`, `profile`, `model`, and `effort` count toward decisions; legacy or incomplete records remain in `observed_n` and source coverage for diagnostics only. `smoke`/`other` must never produce a provider or route hint.
3. A provider hint compares only the current route cell of `selection.default` on both sides; if either provider's raw sample for that role/task-class cell has `n < min_samples` (currently set to 10), the result is **explore** — samples from other profiles/models/efforts must not be pooled to reach the threshold.
4. Only when both sides have sufficient samples does a Beta-posterior `P(win)` reaching the configured threshold (currently 0.90) yield **prefer**; otherwise **either**. Cost tie-breaks are compared only when both sides meet the sample threshold on the same field, and total/output tokens must never be mixed.
5. Rules produce a **hint, not a verdict**; when deviating from the hint, record the reason in `note`.

## Honesty boundaries

- **Counterfactual gap**: the ledger only records dispatches that happened, not a control group of "what if it had been done directly"; dispatch frequency and nested violations are covered separately (and complementarily, without duplication) by the existing `delegation.jsonl` (`delegation-report`).
- **Quality score is subjective**: QS is the main session's judgment and may drift over time; AR/RB/FR are behaviorally defined and therefore more stable.
- **Small samples and task conflation**: every role x task-class x provider cohort is in an exploratory phase until it reaches the policy threshold; even once it does, unpaired tasks still require main-session judgment of difficulty differences.
- **Scenario is not a new role**: role determines permissions; task class determines the comparable cohort; scenario/review lens stays only in the neutral `task` label or the brief. `recon` and `review` under the same role must not be merged for decision purposes.
- **Source is not an interchangeable sample**: the report shows the `request_sources` distribution; native Codex and the Claude plugin bridge may have different context, queueing, and main-session review conditions even when using the same route. When source composition differs noticeably, do not treat aggregated cost as a clean comparison — sample the same brief separately instead.
- **Time contains noise**: `secs` mixes in queueing, approval waits, and human delays; compare mean trends across providers, not single outliers.
- **Cost scope may be incomplete**: legacy records or some providers may lack input/cache tokens, API cost, or human time; the report shows the full proxy only when all fields are present. Subscription plans, latency value, and failure cost still require separate interpretation.
- The ledger is machine-local telemetry and **never enters the database**; the `task` and `note` fields must not contain secrets.
- The pending hook and the outcome logger serialize append/consume through the same lock; overlapping completions still need `dispatch_id` for exact pairing. After validation, the logger cleans up using the first complete stop stub it reads, so a mid-flight new completion does not change the target; but ledger append and pending rewrite are two separate files, so a crash between them can still leave an already-logged stub behind, requiring manual dedup by `dispatch_id`.

## Evolution cadence

Run `experience-report` weekly (can pair with the existing weekly-integrity cadence) and compare against `delegation-report`: when a hint changes, update the preference note in `provider-routing`; for roles with persistently high RB, revisit the brief template or cost-test criteria. `experience-revise` also uses only the route cells within the current deployment profile, to avoid mixing the different risk distributions of fast and quality-guarded routes. Policy adjustments change only the identical `revision_policy` on both sides, never an ad hoc CLI override.
