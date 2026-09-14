---
name: provider-routing
description: |
  Model and role routing — H/X profiles, deployment presets, role selection, security routing, verifier triggers. Load before choosing a named role, before changing a deployment preset, or when deciding if a claim needs an independent verifier.
  觸發：「派給哪個 role」「換 model/effort」「要不要 verifier」「安全審查找誰」。
  不觸發：role 已經定了的直接工作。
---

# Model & Role Routing

Own model/role selection and verifier eligibility. Do not choose dispatch shape or redefine briefs, QC, or record formats here; load `baton-dispatch` before every launch and use its result workflow.

## Model profiles

- The user owns the main-session model and effort through the session selector; tracked settings pin neither. Never switch silently.
- Reference profiles: **H** = Opus/high or Fable/low; **X** = Opus/high or Fable at medium–xhigh. Effort is capped at high for every named role; only the main session under X may raise effort to xhigh.
- Model names are dated operational references, not guarantees. External indices are priors only: prefer the task-relevant model + harness + setting result, then update it with local outcomes.
- Optimize cost per acceptable outcome, not raw token price. Include retries, review/rework, wall-clock, and failure risk. Until a tier reaches the configured sample floor, deliberately explore instead of naming a winner; once sampled, local ledger evidence overrides external priors.
- Claude profiles are **deployment presets**, not per-dispatch routes. Every named role pins model and effort in frontmatter from `selection.default`. For a persistent change, run `main/claude/scripts/model-routing activate-profile --profile <name>` in the source checkout, review it, deploy with `scripts/sync.sh --apply`, then start a new session. The command updates all pins transactionally and `check-pins` verifies the preset. Editing only `~/.claude` is a temporary machine-local override that weekly integrity will report as source drift.

## Role routing

| Role | Use only when |
|---|---|
| `explore` | Broad or bulky read-only search; known-target lookup stays direct |
| `mech-executor` | A complete spec makes the work mechanical |
| `executor` | Isolation or preserved main context repays reconstruction cost |
| `plan-verifier` | A material Plan warrants a fresh Opus challenge |
| `verifier` | A completed claim matches an independent-verifier trigger (below) |
| `security-reviewer` / `security-executor` | Security review (read-only) / approved security implementation |

Named Claude roles own model and effort in frontmatter; omit invocation-level `model` except to sample a second rung deliberately. Security keeps its capability split: review is read-only; implementation starts only from an approved contract. Named-role presets never include Fable. Independent read-only perspectives may run in parallel, but implementation has one writer — never two writers on the same artifacts.

Claude no-write roles lack Bash, so a verdict that depends on running something returns INCONCLUSIVE naming the exact missing check. Commands run by the main session are intermediate evidence, never an independent verdict.

## Route evidence and experience

- After `baton-dispatch` QC, preserve the actual role/profile/model/effort and request source in its fixed records, then log the same route through `experience-ledger`. Record formats and QC mechanics stay in `baton-dispatch`.
- Compare like with like: same role/task class and, where practical, the same brief. Re-sample after a material model, harness, or benchmark change instead of treating an old leaderboard or ledger hint as permanent.

## Independent-verifier triggers

Dispatch at most one outcome `verifier` per top-level task — distinct failure surfaces do not add quota — and only when a trigger in [references/verifier-triggers.md](references/verifier-triggers.md) holds — security/trust boundaries, money, destructive data, adversarial acceptance, conflicting evidence, failed reproduction, or explicit user request. `plan-verifier` returns READY/REVISE; `verifier` returns CONFIRMED/REFUTED/INCONCLUSIVE. Neither has a shell, so a verdict that depends on one names the missing check instead of granting it. Do not stack gates over the same failure surface. A verifier never grades the context that produced the claim: it starts fresh from the claim and the diff.
