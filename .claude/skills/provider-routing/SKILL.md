---
name: provider-routing
description: Cross-provider and role routing for the main session — H/X model profiles, GPT↔Claude fallback rules, codex-rescue bridge usage, security review/implementation routing, and independent-verifier triggers. Load when dispatching to GPT, choosing between named Claude roles and the GPT bridge, handling provider failure/handoff, or deciding whether a completed claim needs a verifier. Not needed for ordinary single-provider direct work.
---

# Provider & Role Routing

## Model profiles

- The user owns the main-session model and effort through the session selector; tracked settings pin neither. Never switch silently.
- Reference profiles: **H** = Fable/low or Opus/high; **X** = Fable/medium or Opus/high. Effort is capped at high everywhere; no role or bridge call uses xhigh.
- Two effort tiers. **Pinned** (`Explore`, `mech-executor`): frontmatter locks effort low — mechanical work whose thinking already happened in main. **Follow** (`executor`, `plan-verifier`, `verifier`, `security-reviewer`, `security-executor`): frontmatter omits effort and inherits the main session's effort, keeping challenge depth symmetric with the work it checks.

## Cross-provider fallback

- Fallback is one cross-provider hop measured from the task's origin. Claude-origin → GPT-5.6 Sol/high, then stop. GPT-origin → the selected Claude profile, then stop. A fallback provider cannot route back.
- Provider fallback is only for provider/runtime unavailability after one bounded retry, persistent in-scope refusal, or two changed attempts with no new evidence. Test failure, missing evidence, approval blocks, and useful diagnostics are NOT provider failures.
- A handoff contains outcome, authorized scope, evidence, attempts, exact failure, artifact paths, prohibitions, and acceptance checks — not a raw transcript.
- GPT bridge calls use `codex:codex-rescue` with explicit `--model gpt-5.6-sol` and `--effort` matching the tier: low for pinned, main-session effort (capped at high) for follow. Read-only work must explicitly prohibit writes (the bridge is write-capable by default).
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

## Dispatch reporting, QC, and provider experience

- Report every dispatch in one fixed line, nothing more: `dispatch: <task> — <role>@<provider> <model>/<effort>`. Codex bridge dispatches are reported the same way as Claude roles.
- Each leaf role has a Codex counterpart (`~/.codex/agents/<role>.toml`), invoked from Claude through the `codex:codex-rescue` bridge: prepend that file's `developer_instructions` as the role contract, pass `--effort` per tier, and for read-only roles prohibit writes.
- Choose per dispatch between the Claude role and its Codex twin — steer by the experience ledger: load `experience-ledger`, log every dispatch outcome after its quality-check (use `--from-pending` to consume the hook-staged stub), and consult its report when provider choice is uncertain. Deviating from a hint requires a logged note.
- QC is tiered by role tier. **Pinned** deliverables (mechanical work from a complete spec) get a spot-check: sample the diff, run the brief's acceptance checks. **Follow** deliverables get a full review against the brief. Either way a weak deliverable is corrected in main or re-briefed, never silently merged.

## Independent-verifier triggers

Dispatch at most one `verifier`, and only when a trigger in [references/verifier-triggers.md](references/verifier-triggers.md) holds — security/trust boundaries, money, destructive data, adversarial acceptance, conflicting evidence, failed reproduction, or explicit user request. `plan-verifier` returns READY/REVISE without Bash; `verifier` returns CONFIRMED/REFUTED and may run read-only checks in an isolated worktree. Do not stack gates over the same failure surface.
