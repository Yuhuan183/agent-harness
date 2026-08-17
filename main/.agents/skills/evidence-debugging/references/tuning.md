# evidence-debugging — agent-harness tuning

Owned by this repo. `SKILL.md` holds what is true of debugging anywhere; this
holds what is true *here*. Upstream rechecks may change `SKILL.md`; they may not
change this file.

This layer does not outrank a system or developer instruction, the current
request, or the global contract. It records defaults this project has found hold
repeatedly, and stop conditions it has paid for.

## Authority

- Being model-invoked is not authority to mutate. Neither is having found the cause.
- The verbs that grant repair: fix, repair, make it work, 修掉, 處理一下, 改掉.
  The verbs that do not: diagnose, explain, why, look into, check, 查一下, 為什麼,
  看一下. Ambiguous is diagnosis only.
- Commit, push, publish, opening an issue and deploying each need their own
  explicit authority, and repair authority does not imply any of them.
- Never dispatch a subagent from inside this skill. If the work genuinely needs
  one, hand it back to the session's dispatch skill and let the existing payoff
  test decide.

## Asking

- Do not ask for what the repo, the logs, the tools or a reproducible probe can
  answer. Look first.
- Ask at most one question, and only when different answers materially change the
  diagnosis. Then say what you will assume if no answer arrives.

## Verification, in this repo's terms

- The narrowest check that could actually refute the claim, not the broadest
  available suite.
- A green test that bypasses the real failing path — the actual parser, file
  system, shell, provider or proxy — cannot close the claim. Say which path
  stayed unexercised.
- **A seam must reach the observable result, not only the action you control.**
  When a check can establish "the request was sent" but not "the effect
  happened", write the second down as uncovered. This rule is local: it came from
  a 2026-08-17 incident where a passing test asserted a launcher exported a
  variable while the setting it was meant to change stayed on, recorded in
  `docs/research/landing-log.md`. Named, not linked — this file is deployed
  outside the repo, where no relative path reaches that tree.
- Non-deterministic defects need a measured reproduction rate quoted before and
  after, not "seems better".

## Reporting

Traditional Chinese (Taiwan) to the user; English for code, identifiers,
commands and any instruction that will be read by another agent.

Lead with the outcome. Then, and only what applies:

- the exact reproduction, or the attempt that failed and what was tried;
- evidence, including the hypotheses that were refuted;
- the change and its verification — only when repair was authorised;
- what remains unverified, and the next observation that would settle it.

Mark a choice the request did not specify as `DECISION: <what and why>`. Mark
uncertainty only where it could change the conclusion.

## Optional tooling

`debug-issue`, the code-review graph, AST search and a browser all accelerate
navigation and none of them are evidence. Without any of them this skill still
works from source, tests, logs and the smallest probe — and correctness never
depends on one being installed.

## Known asymmetry, first release

`agents/openai.yaml` sets `allow_implicit_invocation: false`, so Codex requires
an explicit `$evidence-debugging`. Claude has no equivalent switch — it decides
from the `description`, so on that side implicit invocation stays live. The two
providers therefore differ in how this skill starts, deliberately and only until
description discrimination has been measured. Do not describe the first release
as explicit-only without naming which provider.
