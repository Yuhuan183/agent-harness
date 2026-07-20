---
name: provider-routing
description: Cross-provider and role routing for the main session — H/X model profiles, GPT↔Claude fallback rules, codex-rescue bridge usage, security review/implementation routing, and independent-verifier triggers. Load when dispatching to GPT, choosing between named Claude roles and the GPT bridge, handling provider failure/handoff, or deciding whether a completed claim needs a verifier. Not needed for ordinary single-provider direct work.
---

# Provider & Role Routing

## Model profiles

- The user owns the main-session model and effort through the session selector; tracked settings pin neither. Never switch silently.
- Reference profiles: **H** = Fable/low or Opus/high; **X** = Fable/medium or Opus/xhigh.

## Cross-provider fallback

- Fallback is one cross-provider hop measured from the task's origin. Claude-origin H/X → GPT-5.6 Sol high/xhigh, then stop. GPT-origin → the selected Claude H/X profile, then stop. A fallback provider cannot route back.
- Provider fallback is only for provider/runtime unavailability after one bounded retry, persistent in-scope refusal, or two changed attempts with no new evidence. Test failure, missing evidence, approval blocks, and useful diagnostics are NOT provider failures.
- A handoff contains outcome, authorized scope, evidence, attempts, exact failure, artifact paths, prohibitions, and acceptance checks — not a raw transcript.
- GPT bridge calls use `codex:codex-rescue` with explicit `--model gpt-5.6-sol --effort high|xhigh`. Read-only work must explicitly prohibit writes (the bridge is write-capable by default).
- Before high-complexity/high-intensity dispatch, or materially uncertain provider choice, ask once: `Dispatch GPT + Claude`, `Dispatch GPT`, `Dispatch Claude`. Put the contextual recommendation first, mark it `(Recommended)`, and name H or X.
- Dual-provider review may use independent read-only perspectives. Dual-provider implementation has one writer; the other provider verifies after integration — never two writers on the same artifacts.

## Role routing

| Role | Use only when |
|---|---|
| `Explore` | Broad or bulky read-only search; known-target lookup stays direct |
| `mech-executor` | A complete spec makes the work mechanical |
| `executor` | Isolation or preserved main context repays reconstruction cost |
| `plan-verifier` | A material Plan warrants fresh Opus/high challenge |
| `verifier` | A completed claim matches an independent-verifier trigger (below) |
| GPT security bridge | Primary security review or approved implementation at Sol/high; X requires the user gate |
| `security-reviewer` / `security-executor` | Claude Opus fallback or explicit Claude choice |

Named Claude roles own model and effort in frontmatter; omit invocation-level `model`. Security remains GPT-primary: review is read-only; implementation starts only from an approved contract. GPT failure falls once to the matching Claude Opus role, never Fable. In dual-provider implementation GPT writes and the Claude main session verifies at the selected H/X profile.

## Independent-verifier triggers

Dispatch exactly one `verifier` only when: failure could affect a security/trust boundary, money, destructive data, migrations, concurrency, public APIs, or cross-repo compatibility; judgment-heavy integration cannot be proven mechanically; acceptance depends on adversarial state or boundary behavior; evidence conflicts; reproduction fails; or the user requests it.

Do not dispatch for docs-only, trivial config, decisive mechanical checks, low-risk direct work, or duplicate review. `plan-verifier` returns READY/REVISE without Bash; `verifier` returns CONFIRMED/REFUTED and may run read-only checks in an isolated worktree. Do not stack gates over the same failure surface.
