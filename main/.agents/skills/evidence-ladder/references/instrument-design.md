# Designing a measuring instrument

An L3/L4 probe answers "what does the real thing actually do", in a form a test can assert on. It is a
measuring instrument, so the discipline of any instrument applies. Calibrate it before its readings
count, and do not let it perturb what it measures.

This file is the generic discipline. The concrete harness belongs to the project that owns the
runtime: where probes live, how they connect, and which resources they must not touch. If that
project documents its own probe pattern, follow that for mechanics and this file for judgment.

## What an instrument is for

Reach for one when the claim is about **behaviour you cannot read off the source with confidence**:
geometry, pixels, timing, resource lifetimes, event ordering. If reading the source settles it, read
the source and write one probe as a sentinel instead of many.

Do not build a probe to re-check arithmetic you already own — that is a unit test.

## Shape

**Inputs are exactly the variables you intend to vary.** Every knob you add is a dimension someone can
later confuse for a finding. Start with the two or three you are comparing; add more only when a
question demands it.

**Outputs are raw measurements, never verdicts.** Return positions, sizes, counts, sums — let the
caller decide what is right. You cannot reuse a probe that returns `{ ok: true }` for the next
question, and it hides the number you will need when it disagrees with you.

**Return enough to locate, not just quantify.** "How much" without "where" is unreadable: a total that
says an effect exists cannot tell you it appeared on the wrong side. Include the bounding box, the
index, the offset — whatever answers "where did this come from".

## Isolation

- **Fresh subject per measurement**, disposed after reading. State carried between measurements
  destroys comparability, and you will spend an hour suspecting contamination that was never there.
- **Never share the subject with unrelated fixtures** in the same page or process.
- **Watch for teardown that reaches global state.** Many runtimes have a "release everything" form of
  dispose that also frees shared pools. Using it kills unrelated live instances in the same process.
  Check the dispose signature, pass the narrow form, and leave a comment saying why — this is a
  classic later-simplification landmine.

## Reference frame

The single most common way a probe silently reports nothing: expressing results in a frame derived
from the mechanism under test, so the effect cancels.

Choose an origin you **set directly**, such as the position you assigned or the input you passed. Do
not compute it through the chain you are testing. Write the choice down in the probe's own docs, since
the next reader will otherwise "simplify" it back to the convenient frame.

## Calibration, before any conclusion

Two cases, both required, both committed as tests:

1. **Control** — a subject where the effect should be absent must measure *identical* across the
   configurations that you compare. This catches instruments that always report a difference.
2. **Negative** — a configuration where the mechanism cannot physically produce the effect must read
   as zero. This catches instruments measuring something else entirely.

Keep the control as a **precondition test** beside the real assertions, so a later environment change
invalidates the suite loudly instead of quietly.

## Assert differences, not absolutes

Absolute readings encode the environment: fonts, GPU, DPI, timers, locale. Assertions of the form
"configuration A minus configuration B, same environment, same everything else" survive environment
drift; a hard-coded magnitude does not.

When you must assert an absolute value, pin the environment in the test's own comment. Treat any
future failure as "the environment moved" until evidence shows otherwise.

## What calibration typically catches

The failure worth designing for is not "the probe reads slightly off". It is **the probe reads a
different phenomenon than you think, confidently and precisely**. Two recurring shapes:

- A property of the subject that you did not control for dominates the reading, and the mechanism
  under test contributes nothing to it.
- The reading is an artifact of the measuring environment, which has a different font, codec, clock,
  or precision than the target runtime. It disappears where users actually are.

Both look like clean signal. Only the control and negative cases separate them from a finding.


## The positive control, and why one-liners evade it

An absence claim is only as good as the probe's reach. Before you write "there is
no X", point the same probe at a case that must hit and confirm that it does.
Then report what the probe covered, not only what it returned.

The rule is easy to accept and easy to skip, because an ad-hoc one-liner does
not feel like an instrument. On a single day (2026-08-31), six absence readings
drove action, and each came from a one-liner. The retrospective is in
`docs/research/landing-log.md` of the agent-harness repo. The shapes repeat:

| Shape | What it looked like | What it actually said |
|---|---|---|
| Alphabet or language too narrow | An English-only pattern over a bilingual tree reported zero | Zero *in English*. The rule was there, in the other language |
| Range stopped short | A line window ended five lines above the answer | Nothing in **those lines**, read as nothing in the document |
| Parameter supplied from memory | A threshold and a grouping invented, while an authoritative definition sat one read away | A different question, answered precisely |
| Frames mixed | UTC timestamps compared against a local-time cutoff | An eight-hour window classified backwards |
| Extrapolated past the measurement | Two cohorts existing, read as two cohorts competing | Existence, not competition -- the field that decides it was never read |

Two things make these expensive out of proportion to their size. A silence is
**publishable** in a way a positive is not. A positive finding invites a check
of its own, but an absence tends to go straight into a conclusion. And an
absence claim is usually the *premise of a plan*: "nothing covers this, so
build it". So the error shows up after the work, not before.

The cheap defence is a habit, not a tool: whenever a probe returns nothing,
spend one more command proving it can return something.
