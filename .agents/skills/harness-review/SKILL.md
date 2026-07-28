---
name: harness-review
description: |
  Perform an evidence-first, read-only design review of agent-harness across contract enforcement, control flow, language policy, wording precision, modular ownership, and fixed context overhead. Use for full-repository reviews, bounded path or diff reviews, post-remediation verification, and pre-release audits of routing, dispatch, deployment, hooks, skills, tests, or resident agent contracts. Trigger on requests such as "harness review", "深度 review", "審一下這個 repo 的設計", "全面檢查 agent-harness", or "驗證前次 finding 是否修好". Do not use for other repositories, quick single-file explanations, routine test runs, or implementing fixes. This is a repo-root dev-only skill and must not be added to the deployment manifest.
---

# Harness Review

Review for a decision, not for a long defect list. Determine whether the
reviewed harness is internally coherent, mechanically enforced, traceable,
portable, economical in resident context, and protected by evidence that can
actually refute its claims.

Treat the current checkout and executed mechanisms as truth. Treat prose,
plans, tests, and prior findings as claims to verify. Keep the review
read-only: do not fix findings in the same task.

## Define the review contract

Before inspecting details, record a private contract:

1. Name the exact target: current full checkout, `diff:<range>`,
   `paths:<list>`, or remediation verification.
2. Translate the user's goals into checkable questions.
3. Identify the highest-consequence boundaries in scope.
4. State what evidence would justify `sound`, `fix-first`, or `discuss`.
5. Record important exclusions and validation that the environment cannot
   support.

Default to the current full checkout for a first broad review. For a diff,
read every changed file whole and trace affected consumers, generated copies,
tests, deployment targets, and cleanup or rollback partners. A diff limits
where the investigation starts; it does not limit downstream evidence.

Follow the active top-level orchestration contract. Do not hard-code a model,
provider, dispatch shape, quota rule, latency estimate, or ledger procedure
inside this skill. If an independent verifier is permitted and justified, use
at most one at the smallest coherent integration boundary and give it raw
scope rather than expected findings.

## Establish authority and preserve boundaries

Use authority in this order:

1. The user's current request and active `AGENTS.md` instructions.
2. Repo source under `main/` and root scripts that implement behavior.
3. `scripts/deployment-manifest.tsv` and `scripts/sync.sh` for deployable
   source, target, merge mode, preflight, and parity.
4. Tests and deterministic validators for the exact claim they exercise.
5. README and docs as intended contracts, not implementation proof.
6. Machine-local configuration and live state only when explicitly in scope.

Keep these evidence classes separate:

- **Repository policy**: what the checkout declares.
- **Deployable state**: what the manifest and sync path would install.
- **Machine-local state**: what exists outside the repository.
- **Live state**: what a running service, provider, or UI currently reports.

Never use one class as proof of another. Preserve dirty worktrees and unrelated
user files. Record branch, HEAD, status, scope, and relevant diff before
reviewing.

## Build a coverage ledger

For a full review, read
[references/review-matrix.md](references/review-matrix.md) and cover all six
dimensions. For a bounded review, select the touched dimensions plus every
downstream enforcement, deployment, and validation boundary.

Track:

- claims and their owning files;
- mechanisms that carry and enforce each claim;
- critical flows and state transitions;
- generated, mirrored, or deployed copies;
- tests and probes capable of disproving the claim;
- verified, inferred, and unresolved evidence.

An unopened load-bearing file, untraced consumer, or untested transition is an
explicit review gap, not implicit approval. Use
[references/probes.md](references/probes.md) as a command menu; select only
probes relevant to the contract.

## Match claims to admissible evidence

| Claim | Minimum admissible evidence |
|---|---|
| A rule blocks, rejects, or enforces | Owning text, carrying field or input, executable gate, failure path, and a test or focused probe |
| Routing or fallback is bounded | Configuration plus parser/resolver, identity and hop state, terminal behavior, and adversarial cases |
| Dispatch or approval flow is closed | State transitions, owner at every handoff, stop condition, failure path, and durable observation |
| Deployment is safe and complete | Source ownership, manifest entry, preflight, merge semantics, parity check, and target-specific evidence |
| Language or wording is correct | Audience classification plus all generated, mirrored, and deployed copies |
| Context overhead is bounded | Actual load point, measured payload in a meaningful unit, and a limit that cannot be trivially gamed |
| A test protects runtime behavior | Assertions and fixtures preserve the load-bearing semantics; a green name or mocked path is insufficient |
| Current machine or provider behavior | Current host-side or provider-side observation; repository text alone is insufficient |

Label conclusions:

- **Verified**: directly supported by current source, execution, or a
  reproducible probe.
- **Inferred**: likely impact derived from verified facts; state the inference.
- **Unresolved**: the required evidence or environment was unavailable.

## Trace mechanisms end to end

For each important control, trace:

`declaration → carrier → parser → decision gate → side effect → observable result → failure or rollback → regression gate`

For each important workflow, trace:

`request → classification → owner → state transition → handoff → stop condition → durable record`

Attack each chain with the cases that apply: absent, malformed, contradictory,
duplicate, delayed, failed, retried, cancelled, concurrent, stale,
machine-local-only, and partially deployed. Check bootstrap order explicitly:
a deployment preflight must not depend on the already-deployed copy it is
supposed to validate.

When timing, state, merge behavior, shell semantics, or provider behavior
matters, construct the smallest controlled probe that can falsify the claim.
Static search is discovery, not proof. Remove temporary artifacts before
finishing.

## Qualify findings adversarially

Before retaining a finding:

1. Read the whole relevant file and both sides of the boundary.
2. Name the exact violated contract and its owner.
3. Give a concrete input or event sequence that causes wrong behavior,
   bypass, contradiction, unsafe deployment, excess resident cost, or likely
   operator misuse.
4. Search for a guard, later-stage check, generated source, test, or documented
   precondition that refutes the candidate.
5. Reproduce it when the claim depends on execution, ordering, merge behavior,
   or external state.
6. State the smallest coherent fix direction and the regression gate that
   would catch it.

Drop candidates that remain merely plausible or stylistic. Record meaningful
refutations so the report shows what was challenged without padding the
finding list.

## Evaluate validation as a protection system

Map every claim to the narrowest layer that can refute it:

- syntax, schema, lint, and static contract checks;
- focused unit tests for parsers, validators, routing, and state transitions;
- shell integration tests for quoting, exit codes, environment, and installer
  behavior;
- deployment dry-run, merge, backup, and parity checks;
- host-side service or UI checks for machine-local and live-state claims;
- controlled provider or network checks only when required and authorized.

Inspect assertions, not test names. Mocks that bypass the actual parser,
filesystem, shell, provider, or deployed target cannot prove those boundaries.
Report exact commands, outcomes, retries, environment-only failures, and
skipped layers. Never convert a green static suite into proof of runtime
effectiveness.

## Converge

Use impact-based severity:

- **Critical**: a primary safety boundary can be bypassed; destructive or
  secret-bearing behavior can escape scope; deployment can corrupt broad user
  state; or routing can run unbounded.
- **Major**: a reproducible contradiction, failed guard, broken handoff,
  bootstrap dependency, incorrect deployment result, or material contract
  drift affects a normal path.
- **Minor**: a verified precision, maintainability, language, test-quality, or
  context-cost defect has limited operational impact.

Do not inflate severity to match review breadth and do not manufacture
findings to fill every dimension.

## Output

Write the user-facing report in Traditional Chinese with Taiwan terminology.
Lead with:

1. Verdict: `sound`, `fix-first`, or `discuss`, and the controlling reasons.
2. Ranked, deduplicated findings.
3. Refuted or dropped material candidates.
4. What is solid, mapped to the review contract.
5. Validation evidence by layer.
6. Remaining scope, host, provider, or runtime limits.
7. Recommended remediation and verification order when not `sound`.

Format each finding as:

```text
F-NN · Critical|Major|Minor · dimension
Evidence: file:line plus command or observed behavior
Contract: the exact rule or invariant
Failure: the concrete sequence and impact
Fix: the smallest coherent direction
Gate: the regression check that should fail before the fix
```

End with `SOUND`, `NEEDS-WORK`, or `UNRESOLVED` for each of the six
dimensions, with one evidence-based sentence. Do not implement fixes; treat
remediation as a separate task and re-review its exact diff afterward.
