---
name: provider-routing
description: Cross-provider and role routing for the main session — H/X model profiles, GPT↔Claude fallback rules, codex-rescue bridge usage, security review/implementation routing, and independent-verifier triggers. Load when dispatching to GPT, choosing between named Claude roles and the GPT bridge, handling provider failure/handoff, or deciding whether a completed claim needs a verifier. Not needed for ordinary single-provider direct work.
---

# Provider & Role Routing

## Model profiles

- The user owns the main-session model and effort through the session selector; tracked settings pin neither. Never switch silently.
- Reference profiles: **H** = Fable/low or Opus/high; **X** = Fable/medium or Opus/high. Effort is capped at high everywhere; no role or bridge call uses xhigh.
- Role effort has two tiers. **Pinned** (`Explore`, `mech-executor`): frontmatter locks effort low — mechanical work whose thinking already happened in main. **Follow** (`executor`, `plan-verifier`, `verifier`, `security-reviewer`, `security-executor`): frontmatter omits effort and inherits the main session's effort — roles with genuine autonomous-thinking needs, so challenge depth stays symmetric with the work it checks.

## Cross-provider fallback

- Fallback is one cross-provider hop measured from the task's origin. Claude-origin → GPT-5.6 Sol/high, then stop. GPT-origin → the selected Claude profile, then stop. A fallback provider cannot route back.
- Provider fallback is only for provider/runtime unavailability after one bounded retry, persistent in-scope refusal, or two changed attempts with no new evidence. Test failure, missing evidence, approval blocks, and useful diagnostics are NOT provider failures.
- A handoff contains outcome, authorized scope, evidence, attempts, exact failure, artifact paths, prohibitions, and acceptance checks — not a raw transcript.
- GPT bridge calls use `codex:codex-rescue` with explicit `--model gpt-5.6-sol` and `--effort` matching the tier: low for pinned roles, the main session's effort (capped at high) for follow roles. Read-only work must explicitly prohibit writes (the bridge is write-capable by default).
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
| GPT security bridge | Primary security review or approved implementation at Sol/high |
| `security-reviewer` / `security-executor` | Claude Opus fallback or explicit Claude choice |

Named Claude roles own model and effort in frontmatter; omit invocation-level `model`. Security remains GPT-primary: review is read-only; implementation starts only from an approved contract. GPT failure falls once to the matching Claude Opus role, never Fable. In dual-provider implementation GPT writes and the Claude main session verifies at the selected profile.

## Dispatch reporting and provider experience

- Report every dispatch to the user before or as it launches: task, provider (Claude role or Codex bridge), model, and effort. Codex bridge dispatches are reported the same way as Claude roles.
- Each leaf role has a Codex counterpart (`~/.codex/agents/<role>.toml`), invoked from Claude through the `codex:codex-rescue` bridge: prepend that file's `developer_instructions` as the role contract in the brief, pass `--effort` per the tier above, and for read-only roles instruct a read-only run and prohibit writes. Standalone Codex sessions use the same files natively as custom agents.
- Choose per dispatch between the Claude role and its Codex twin. No fixed provider per role — steer by the experience ledger: load `experience-ledger`, log every dispatch outcome after its quality-check, and consult its report when provider choice is uncertain. Deviating from a hint requires a logged note.
- The main session quality-checks every subagent deliverable against the brief before integration; a weak deliverable is corrected in main or re-briefed, never silently merged.

## Independent-verifier triggers

Dispatch exactly one `verifier` only when: failure could affect a security/trust boundary, money, destructive data, migrations, concurrency, public APIs, or cross-repo compatibility; judgment-heavy integration cannot be proven mechanically; acceptance depends on adversarial state or boundary behavior; evidence conflicts; reproduction fails; or the user requests it.

Do not dispatch for docs-only, trivial config, decisive mechanical checks, low-risk direct work, or duplicate review. `plan-verifier` returns READY/REVISE without Bash; `verifier` returns CONFIRMED/REFUTED and may run read-only checks in an isolated worktree. Do not stack gates over the same failure surface.
