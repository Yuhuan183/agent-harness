---
name: provider-routing
description: Cross-provider routing — H/X profiles, GPT↔Claude fallback, codex bridge resolution, security routing, verifier triggers. Load before dispatching to GPT, on provider failure/handoff, or when deciding if a claim needs a verifier. Not for single-provider direct work.
---

# Provider & Role Routing

## Model profiles

- The user owns the main-session model and effort through the session selector; tracked settings pin neither. Never switch silently.
- Reference profiles: **H** = Fable/low or Opus/high; **X** = Fable at medium–xhigh or Opus/high. Effort is capped at high for every named role and bridge call; only the main session under X may raise effort to xhigh.
- Model names are dated operational references, not guarantees. External indices are priors only: prefer the task-relevant model + harness + setting result, then update it with local outcomes.
- **Provider choice is CP-first**: compare only the same role and non-smoke task class. Until each side reaches the configured sample floor, deliberately explore instead of naming a winner. Once sampled, local ledger evidence overrides external priors. A usage alarm — Codex via `codex-usage --quota`, Claude via `/usage` — may switch to the provider with headroom; ask via the three-option gate when material.
- Optimize cost per acceptable outcome, not raw token price. Include retries, review/rework, wall-clock, and failure risk. Compare a cost field only when both providers have the same coverage; never compare one side's total tokens with the other's output-only tokens.
- Claude profiles are **deployment presets**, not per-dispatch routes. Every named role pins model and effort in frontmatter from `selection.default`. For a persistent change, run `.claude/scripts/model-routing activate-profile --profile <name>` in the source checkout, review it, deploy with `scripts/sync.sh --apply`, then start a new session. The command updates all pins transactionally and `check-pins` verifies the preset. Editing only `~/.claude` is a temporary machine-local override that weekly integrity will report as source drift. Codex native and bridge routes remain per-dispatch and do not change Claude pins or main model.
## Codex bridge profile resolution

- Before every `codex:codex-rescue` leaf dispatch, normalize `Explore` to `explore`, then run `${CODEX_HOME:-$HOME/.codex}/scripts/model-routing resolve --surface claude-bridge --priority <priority> --role <role>`. Parse its JSON and pass the returned `model` and `effort` explicitly. Prepend `~/.codex/agents/<role>.toml`'s `developer_instructions` as the role contract; read-only roles must still explicitly prohibit writes because the bridge is write-capable by default. `~/.codex/scripts/bridge-brief <role> [--priority <p>]` emits the resolved override plus role contract as a brief skeleton — prefer it over hand-assembling.
- Choose one priority per dispatch from the three profiles: `balanced` by default; `fast` for time-sensitive or output-token-sensitive work; `quality-guarded` only for high-risk, high-impact, or highly uncertain work. Quality floors remain mandatory. There is no economy profile: usage/cost protection is handled by the provider-choice layer above, never by degrading a route.
- The resolver is the single source of truth for Codex bridge model and effort. Do not apply Claude preset pins afterward, and do not silently replace a resolver result with a hard-coded model. A missing, invalid, or non-dispatchable routing artifact is a deployment/configuration error: report it and do not launch that Codex leaf.
- The routing file records availability per surface. `documented` subscription/main-selector access does not prove leaf override support; only `claude_bridge_override = "configured"` may be returned for this bridge. Benchmark rows with an `unverified` bridge override remain comparison data, not dispatch routes.
## Cross-provider fallback

- Fallback is one cross-provider hop measured from the task's origin. Claude-origin → the Codex route resolved for the role and selected priority, then stop. GPT-origin → the active Claude deployment preset, then stop. A fallback provider cannot route back.
- Provider fallback is only for provider/runtime unavailability after one bounded retry, persistent in-scope refusal, or two changed attempts with no new evidence. Test failure, missing evidence, approval blocks, and useful diagnostics are NOT provider failures.
- A handoff contains outcome, authorized scope, evidence, attempts, exact failure, artifact paths, prohibitions, and acceptance checks — not a raw transcript.
- GPT bridge calls use `codex:codex-rescue` with the resolver's explicit `--model <model>` and `--effort <effort>` values. High-risk security and verifier routes resolve to Sol/high under the current quality floors.
- Before high-complexity/high-intensity dispatch, or materially uncertain provider choice, ask once: `Dispatch GPT + Claude`, `Dispatch GPT`, `Dispatch Claude`. Put the contextual recommendation first, mark it `(Recommended)`, and name H or X.

## Role routing

| Role | Use only when |
|---|---|
| `Explore` | Broad or bulky read-only search; known-target lookup stays direct |
| `mech-executor` | A complete spec makes the work mechanical |
| `executor` | Isolation or preserved main context repays reconstruction cost |
| `plan-verifier` | A material Plan warrants a fresh Opus challenge |
| `verifier` | A completed claim matches an independent-verifier trigger (below) |
| `security-reviewer` / `security-executor` | Security review (read-only) / approved security implementation; provider by CP-first choice, either side routes at its critical floor |

Named Claude roles own model and effort in frontmatter; omit invocation-level `model`. Security keeps its capability split on either provider: review is read-only; implementation starts only from an approved contract. Dual-provider review may use independent read-only perspectives; implementation has one writer — never two writers on the same artifacts. Cross-provider fallback is one hop to the matching role on the other provider — on Claude that means Opus, never Fable. In dual-provider implementation one provider writes and the other verifies after integration.

## Dispatch reporting, QC, and provider experience

- Report each launch as its own fixed record, not prose: `[LEAF_DISPATCH] task=<label> | role=<role> | class=<class> | source=<source> | route=<profile>/<provider>/<model>/<effort> | reason=<parallelism|context-protection|fresh-context|cheaper-tier>`. After main-session QC, report `[LEAF_RESULT] task=<same-label> | outcome=<accepted|corrected|rebriefed|failed> | qc=<spot|full> | ledger=<logged|skipped(reason)>`. Use a neutral task label and ledger class, state only the active/resolved profile, and never claim `logged` before success.
- Each leaf role has a Codex counterpart (`~/.codex/agents/<role>.toml`), invoked from Claude through the `codex:codex-rescue` bridge using the structured resolution procedure above. This routing controls only the Codex twin; it never changes the Claude main-session model or the named Claude role frontmatter.
- Load `experience-ledger` and log every dispatch outcome after QC. Hooks record `claude-code` or `claude-code-plugin-codex`; native Codex records use `codex`. Always retain task class and resolved profile. If concurrent completions exist, pass the exact `--dispatch-id` rather than consuming the latest guess. Deviating from a hint requires a logged note.
- Provider extension (e.g. Gemini) follows [references/provider-protocol.md](references/provider-protocol.md): shared-schema routing file, `routing_core` resolver wrapper, explicit-override leaf with machine-verifiable telemetry, ledger and quota integration; cross-platform leaf calls only where the platform officially supports them.
- Compare like with like: same role/task class and, where practical, the same brief. Re-sample after a material model, harness, or benchmark change instead of treating an old leaderboard or ledger hint as permanent.
- Codex cost telemetry lives in local session rollouts, not the plugin output: `experience-ledger`'s `codex-usage` script reports per-turn tokens and the account quota snapshot. Check quota before heavy Codex dispatch; the short window (e.g. 5h) outranks the weekly one — exhausting it stalls tasks immediately — so when the short window is near its limit, prefer the Claude role or wait for its reset, regardless of weekly headroom.
- QC is tiered by task shape: mechanical work from a complete spec gets a spot-check (sample the diff, run the brief's acceptance checks); judgment-heavy or verification deliverables get a full review against the brief. Either tier hunts false-completion frauds: weakened or bypassed checks, fixtures fabricated to satisfy a check, undeclared out-of-scope changes, missing owed `INTENT:`/`TWINS:`/`AUTH:` lines, and leftover leaf-created scratch files (pre-existing dirty-worktree files are not debris). A weak deliverable is corrected in main or re-briefed, never silently merged.

## Independent-verifier triggers

Dispatch at most one `verifier`, and only when a trigger in [references/verifier-triggers.md](references/verifier-triggers.md) holds — security/trust boundaries, money, destructive data, adversarial acceptance, conflicting evidence, failed reproduction, or explicit user request. `plan-verifier` returns READY/REVISE without Bash; `verifier` returns CONFIRMED/REFUTED/INCONCLUSIVE and may run read-only checks in an isolated worktree. Do not stack gates over the same failure surface.
