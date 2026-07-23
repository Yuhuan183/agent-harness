# Provider Extension Protocol

What a new provider (e.g. Google Gemini) must supply before it becomes a routable
dispatch target. The goal is the quality/speed/cost triangle across agent
platforms: any platform can call another provider's model as a leaf agent when
the platform officially supports it; when it does not, that platform stays
single-provider and this protocol does not apply there.

## Required artifacts

1. **Routing file** — `<provider-dir>/model-routing.toml` in the shared
   structural schema (`selection` with three profiles: balanced / fast /
   quality_guarded, `route_application.roles`, `quality_floor`, `profiles`,
   executable `revision_policy`). Per-surface `availability` keys are provider-specific;
   benchmark metrics use whatever granularity the provider's evaluations
   publish, marked as priors.
2. **Resolver wrapper** — `<provider-dir>/scripts/model-routing` importing
   `.agents/scripts/routing_core.py` for selection/floor/profile validation and
   profile resolution; provider-specific schema stays in the wrapper. A missing
   core is a deployment error, never a silent fallback.
3. **Leaf invocation mechanism** — a bridge or native spawn that accepts an
   explicit model/effort override per dispatch, plus machine-verifiable
   telemetry (rollout-equivalent) so smoke evidence is provider-recorded, not
   agent-self-reported. Availability stays `unverified` until a dated,
   telemetry-backed smoke test is recorded in the routing file.
4. **Ledger integration** — a provider name in `experience-log`, a distinct
   `request_source`, route/profile/dispatch/telemetry identifiers, comparable
   task classes, and inclusion in `experience-revise`'s config list.
5. **Quota probe** — a `codex-usage`-equivalent reading local, provider-recorded
   usage; short-window alarms feed the CP-first switch rule. No probe → the
   provider cannot participate in usage-based switching and heavy dispatch to
   it requires manual confirmation.
6. **Fallback membership** — single-hop rule extends pairwise: a failed dispatch
   falls once to the CP-next provider's matching role, then stops. Never
   circular, and a fallback provider cannot route onward.

## Non-negotiables

- Quality floors are per-provider but every provider must define all three
  tiers (support / judgment / critical) over its own models.
- Model/effort always come from the provider's own routing profile; the
  CP-first layer chooses the provider, never the route.
- External benchmarks enter as priors only; local ledger evidence re-derives
  profiles per each file's validated `revision_policy`. Smoke/other cohorts and
  mismatched telemetry scopes never drive a provider or route preference.
