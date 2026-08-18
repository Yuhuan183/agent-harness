---
name: test-first-change
description: Add or change behaviour by writing the check that fails first, at a seam that reaches the observable result. Invoke when the request asks to implement, add, change or extend behaviour, to write or repair a test, or names TDD or test-first — and in zh-TW: 實作, 加上, 改掉, 擴充, 補測試, 修測試. Do not use for an unexplained defect (diagnose it first with evidence-debugging), for formatting or documentation-only edits, or for a change nothing could have failed on beforehand.
---

# Test-First Change

A check written after the code is a check shaped to pass. This skill exists to
stop one move: shipping an assertion that could not have failed.

Derived from Matt Pocock's [`tdd`](https://github.com/mattpocock/skills); see
`ATTRIBUTION.md` for the reviewed commit, licence, and what was changed. This
repo's verification surfaces, worked good and bad examples, authority rules and
reporting shape are in `references/tuning.md`. For repo structure read
`AGENTS.md` and `docs/architecture.md` — this skill never creates a new context
document.

## Seam, defined here

A **seam** is a boundary a check can call without reaching inside the thing
under test: a public signature, a CLI invocation, an HTTP request, a file the
code writes, an exit status. Not a seam: a private helper, an internal variable,
a mocked collaborator, a log line.

Two properties decide whether it is the right seam.

- **Reach** — exercising it runs the code that would carry the defect.
- **Observability** — its result is what the request is about, not a step on the
  way there.

Reach without observability is the trap: the check passes, the code ran, and
nothing says the outcome happened. Take the outermost seam that still fails
fast; go deeper only when the outer one cannot tell the change apart.

Derive the seam from the code and the repo's existing test layout. Ask only when
two candidates would produce materially different checks and nothing on disk
decides between them — then name both and say which you will use if no answer
arrives.

## The gate

**Before writing the implementation, run the new check and watch it fail.**
Quote the failure. Two things make it the right failure:

- **the predicted reason** — the assertion that fires is the one about the new
  behaviour, not an import error, a typo or a missing fixture;
- **absent behaviour, not absent scaffolding** — failing because a function does
  not exist yet is a compile error wearing a test's name.

It then has to pass on the real implementation, not on a stub shaped to satisfy
it. No observed failure, no implementation. If the behaviour cannot be made to fail
on demand, say so, name the seam you tried, and ask for what would make it
reachable — do not write the code and add a check afterwards to cover the gap.

## Four ways an assertion cannot fail

1. **Tautological** — it recomputes what the code computes, so the two can never
   disagree: `expected = build(x)` beside `assert build(x) == expected`.
2. **Guaranteed by construction** — the setup makes the condition true. A check
   that a launcher exports a variable, when exporting it is the launcher's whole
   job, restates the source in another language.
3. **Reaches your action, not the outcome** — it proves the request was sent,
   the flag was set, the file was written. Whether the effect landed stays
   uncovered; write that down rather than letting green speak for it.
4. **Never seen red** — the behaviour was never produced on demand, so passing
   says only that nothing was observed.

One question catches all four: *what would I change to make this fail?* If
nothing in the code answers, the check describes the code instead of
constraining it.

## Mocking

Mock what you neither own nor can run: a paid API, a clock, a remote host. Never
mock the thing under test, and never mock the layer where the defect would live
— the real parser, filesystem, shell, provider or proxy is the point. If a seam
is only testable with the failing path mocked out, that absence is the finding:
report it instead of a green that bypassed the code.

## Then

1. **Write the check.** One behaviour, named after it. Assert the observable
   result, not the sequence of calls that produced it, and take the expected
   value from a source independent of the code — a known literal, a worked
   example, the spec.
2. **Watch it fail**, against the gate above.
3. **Implement the smallest change that turns it green.** Not the general
   version — the next check earns that. One check, one implementation, then
   repeat: each slice is a tracer bullet that answers what the last one taught,
   and a slice that delivers no observable behaviour is half a layer, not a slice.
4. **Re-run the narrow suite**, then the wider one this change could reach.
5. **Keep the check**, in the repo's existing conventions rather than a parallel
   style of your own.

A change is finished when the check fails without it and passes with it,
existing checks still pass, temporary fixtures are gone, and any behaviour left
uncovered is written down as uncovered rather than quietly omitted.

## Never

- Weaken, skip or delete an existing assertion to make a change pass. A check in
  the way is a decision to raise, not an obstacle to clear.
- Write every planned check up front. Each cycle changes what the next one
  should say.
- Commit, push, publish or deploy. Those need their own authority.
- Dispatch a subagent from here. Hand it back to the session's dispatch skill.
- Count a type checker, linter or coverage number as the failing check. They
  constrain shape; they do not observe behaviour.
