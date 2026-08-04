# Harness review matrix

Use this matrix to keep full reviews broad without becoming shallow. For
bounded work, select the dimensions touched by the change and every downstream
enforcement, deployment, and validation boundary.

## Contents

- Contract and logic chain
- Flow and state closure
- Language and audience policy
- Wording and semantic precision
- Modularity, sharing, and deployment ownership
- Resident context and fixed overhead
- Cross-cutting validation closeout

## 1. Contract and logic chain

### Core question

Does every material promise have one owner and an executable mechanism that
makes the promise true?

### Inspect

- Map normative words such as `must`, `never`, `only`, `block`, `reject`, and
  `enforce` to a parser, carrying field, gate, exit status, sandbox boundary,
  or deployment preflight.
- Verify the gate covers absent, malformed, contradictory, negative,
  non-finite, duplicated, stale, and unsupported values where applicable.
- Trace defaults from declaration through parsing, override precedence,
  resolution, and observable output.
- Compare Claude and Codex only where they implement the same portable
  contract; distinguish intentional platform differences from drift.
- Verify a preflight reads repository-owned source rather than the installed
  target it is supposed to validate.
- Check that warnings are not described as blockers and advisory hooks are not
  described as enforcement.

### High-risk patterns

- Fail-open hooks paired with reject language.
- The same routing question answered in two files with no declared precedence.
- Validation that rejects one invalid sibling but accepts the rest.
- A default documented at one layer and silently replaced at another.
- Bootstrap self-dependency on HOME or an already-deployed skill.

### Evidence to close

Require the owning contract, the complete executable chain, a concrete bypass
attempt, and the narrowest regression gate.

## 2. Flow and state closure

### Core question

Can every workflow be drawn as a closed state graph with an owner, carrying
state, terminal result, and failure path at every edge?

### Inspect

- Trace request classification, plan or execution state, dispatch, fallback,
  quality check, approval, apply, logging, and completion where present.
- Verify prose invariants have actual fields or artifacts that survive the
  handoff: origin, hop count, task identity, scope, owner, result, and status.
- Identify retries, cancellation, timeouts, stale completions, and concurrent
  runs.
- Check that a verifier receives the correct integration boundary and cannot
  silently broaden scope or become a second owner.
- Verify `blocked`, `complete`, `accepted risk`, and `unresolved` have distinct
  entry conditions and observable outcomes.
- Check feedback loops include consent, approval, apply, verification, and
  durable recording when those steps are claimed.

### High-risk patterns

- "Single-hop" fallback with no hop or origin state.
- A handoff that loses scope, identity, or acceptance criteria.
- A loop ending at "suggestion" despite claiming continuous improvement.
- A failure branch that has no wake-up, retry, or terminal state.
- Two agents or scripts owning the same writable artifact.

### Evidence to close

Build the state or sequence diagram, then probe at least one failure,
duplicate, stale, or concurrent transition on each critical flow.

## 3. Language and audience policy

### Core question

Does each artifact use the language, terminology, and punctuation appropriate
to its actual consumer?

### Inspect

- Classify content as runtime agent-consumed, code-adjacent, human-facing,
  generated, or mirrored before judging language.
- Keep runtime agent text, code, identifiers, commands, comments, and commit
  messages in English.
- Keep human-facing explanations in Traditional Chinese with Taiwan
  terminology unless a more specific contract overrides it.
- Check generated and deployed copies, not only the source file.
- Verify examples preserve literal identifiers and commands while surrounding
  explanation follows the audience policy.
- Distinguish harmless bilingual naming from mixed terminology that changes
  interpretation.

### High-risk patterns

- Chinese runtime instructions that reduce cross-provider consistency.
- PRC vocabulary in Taiwan-facing docs.
- Translated identifiers or shell fragments that no longer execute.
- A source corrected while a generated or deployed mirror remains stale.
- Punctuation rules applied globally without regard to audience.

### Evidence to close

Show the audience classification, owning policy, all relevant copies, and a
targeted terminology sweep.

## 4. Wording and semantic precision

### Core question

Does one term have one operational meaning, with cardinality, precedence,
units, and exceptions defined exactly once?

### Inspect

- Compare definitions across contracts, routing config, skills, role files,
  docs, schemas, tests, and error messages.
- Expand load-bearing acronyms at first use or link them to one definition.
- Make `exactly one`, `at most one`, `one or more`, ordered fallback, and stack
  semantics explicit and consistent.
- Verify `default`, `recommended`, `required`, `available`, `supported`,
  `blocked`, and `complete` match executable behavior.
- State units and counting rules for time, quota, context, hops, retries, and
  budgets.
- Check negative claims such as `never`, `only`, and `cannot` against every
  implementation path.

### High-risk patterns

- The same field name used for origin, current provider, and fallback target.
- "Available" meaning any surface in one file and all surfaces in another.
- A line budget presented as a context budget.
- Historical rationale written as a current invariant.
- Exact-string tests coupled to incidental line wrapping or file placement.

### Evidence to close

Identify the canonical definition, enumerate consumers, and show the concrete
misclassification or operator decision caused by drift.

## 5. Modularity, sharing, and deployment ownership

### Core question

Does each concern have one source of truth, the correct owner, a stable
dependency direction, and an explicit deployment boundary?

### Inspect

- Separate portable policy, platform adapter, provider-specific routing,
  machine-local installer state, and live service state.
- Verify deployable artifacts originate under `main/`; keep repo-root
  `.agents/skills/` and other dev-only material out of the manifest.
- Trace manifest source, target, mode, preflight, backup, merge behavior, and
  parity check.
- Identify hand-copied twin contracts and require generation, shared source, or
  semantic parity tests when they express the same rule.
- Confirm installed examples, tests, and plans are actually read at runtime;
  otherwise keep them dev-only.
- Check that personal preferences do not leak into portable shared settings.
- Verify helper scripts depend downward on stable interfaces rather than
  reading arbitrary HOME state.

### High-risk patterns

- Two writable owners for the same artifact.
- Platform-neutral policy duplicated in provider-specific files.
- Dev-only files included in deployment "for convenience".
- Merge behavior preserving stale target keys with no visibility.
- Deployment validation that passes only after a previous successful
  deployment.

### Evidence to close

Trace one concern from source through manifest and installed target, including
merge and rollback semantics. Keep current live-state conclusions separate.

## 6. Resident context and fixed overhead

### Core question

Is always-loaded work minimal, measurable in the right unit, hard to game, and
paid only where it changes behavior?

### Inspect

- Locate actual load points for resident contracts, agents, hooks, skills,
  generated prompts, probes, and caches.
- Distinguish fixed per-session cost from conditional skill cost, tool output,
  cached input, and one-time deployment work.
- Measure bytes, words, tokens, lines, calls, or latency according to the
  claimed budget; do not substitute a convenient proxy silently.
- Compare equivalent Claude and Codex behavior only after accounting for
  platform loading differences.
- Move detailed examples, historical incidents, and variant-specific guidance
  behind progressive disclosure when they are not needed on every run.
- Verify caches have an invalidation key and that probes are not repeated
  without changing the decision.
- Recalibrate every threshold when the counting unit or tokenizer changes.

### High-risk patterns

- Line-count limits defeated by arbitrarily long lines.
- The same rule resident in contracts, role files, and skills.
- Provider-specific incident history embedded in a permanent workflow.
- Hooks re-probing stable facts on every session.
- A "smaller" prompt that merely moves content into another always-loaded
  artifact.

### Evidence to close

Show the load point, measured cost, decision value, evasion cases, and the
smallest progressive-disclosure boundary that preserves correctness.

## Cross-cutting validation closeout

Before concluding:

- Map every user quality goal to verified evidence, a finding, or an explicit
  unresolved limit.
- Inspect assertions and fixtures for each regression gate cited.
- Distinguish repository tests from deployment parity, host state, provider
  behavior, UI state, and network behavior.
- Record meaningful candidates that were refuted by guards or tests.
- Recheck terminology and mirrored copies after any remediation review.
- Confirm no temporary probe or generated review artifact remains.
- Recheck worktree status and preserve the user's original unrelated changes.
