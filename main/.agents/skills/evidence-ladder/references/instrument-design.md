# Designing a measuring instrument

An L3/L4 probe answers "what does the real thing actually do", in a form a test can assert on. It is a
measuring instrument, so it is subject to the same discipline as any instrument: it must be calibrated
before its readings count, and it must not perturb what it measures.

This file is the generic discipline. The concrete harness — where probes live, how they are wired, and
which resources they must not touch — belongs to the project that owns the runtime; if that project
documents its own probe pattern, follow that for mechanics and this for judgment.

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
caller decide what is right. A probe that returns `{ ok: true }` cannot be used for the next question,
and hides the number you will need when it disagrees with you.

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

Choose an origin you **set directly** — the position you assigned, the input you passed — not one you
compute through the chain you are testing. Write the choice down in the probe's own docs, since the
next reader will otherwise "simplify" it back to the convenient frame.

## Calibration, before any conclusion

Two cases, both required, both committed as tests:

1. **Control** — a subject where the effect should be absent must measure *identical* across the
   configurations being compared. This catches instruments that always report a difference.
2. **Negative** — a configuration where the mechanism cannot physically produce the effect must read
   as zero. This catches instruments measuring something else entirely.

Keep the control as a **precondition test** beside the real assertions, so a later environment change
invalidates the suite loudly instead of quietly.

## Assert differences, not absolutes

Absolute readings encode the environment: fonts, GPU, DPI, timers, locale. Assertions of the form
"configuration A minus configuration B, same environment, same everything else" survive environment
drift; a hard-coded magnitude does not.

When an absolute value must be asserted, pin the environment in the test's own comment, and treat any
future failure as "the environment moved" until proven otherwise.

## What calibration typically catches

The failure worth designing for is not "the probe reads slightly off". It is **the probe reads a
different phenomenon than you think, confidently and precisely**. Two recurring shapes:

- The reading is dominated by a property of the subject you did not control for, and the mechanism
  under test contributes nothing to it.
- The reading is an artifact of the measuring environment — a different font, codec, clock, or
  precision than the target runtime — and disappears where users actually are.

Both look like clean signal. Only the control and negative cases separate them from a finding.
