---
name: evidence-ladder
description: |
  Establish that a technical claim is true — pick the cheapest sufficient level of evidence, avoid circular proof, calibrate instruments before trusting them, and record conclusions at the right durability.
  觸發：「這個結論可靠嗎」「怎麼證明」「測試夠不夠」「我推導出 X」、下結論前的自我檢查、要把量測數字寫進文件、發現先前結論可能有誤。
  不觸發：例行實作沒有爭議的結論、單純跑既有 gate、程式碼審查流程本身（用該專案的 review skill）。
---

# Evidence Ladder

A claim is only as good as the level of evidence under it. This skill picks that level deliberately,
then guards the three ways evidence silently fails: it is circular, the instrument is uncalibrated, or
it was gathered somewhere the claim does not apply.

Use it when you are about to **assert something as true** — in a reply, a code comment, a doc, or a
commit message — and being wrong would cost real work.

## 1. The ladder

| Level | Proves | Cannot prove | Cost |
|---|---|---|---|
| L0 Reasoning from docs/memory | Nothing on its own | Anything | free |
| L1 Read the installed source | What the code says | That it executes that way here | minutes |
| L2 Unit test against a mock/fake | Your arithmetic over your model | **That the model matches reality** | minutes |
| L3 Probe the real dependency | The model, in isolation | That the integration wires it up | ~hour |
| L4 End-to-end through your own path | The integration | That the target environment agrees | hours |
| L5 Target runtime / real consumer | What users get | — | needs the other side |

Two rules read straight off the table:

- **Never state an engine/library *semantic* on L2 alone.** A mock replays the model you wrote into it,
  so it agrees with you by construction. L2 is for *your* arithmetic, never for *their* behaviour.
- **L1 is not a substitute for L3, but it often replaces repeated L3.** If the source has no branch on
  a variable, you do not need to measure every value of that variable — read once, then pin the
  behaviour with one L3 probe as a sentinel.

## 2. Choosing the level

Pick by what a wrong answer costs, not by what is convenient:

- Claim only affects this conversation → L1.
- Claim becomes a code change → L2 for your arithmetic **plus** L3 for every engine semantic the
  arithmetic depends on.
- Claim becomes a compensation for third-party internals → L3 as a **sentinel test**, phrased so it
  fails if the dependency changes its behaviour. State in the test why: the behaviour is an
  implementation detail, not a contract.
- Claim changes what users see or where things land → L4, and name the L5 that is still outstanding.
- Absolute measured numbers headed for shipped docs → L5, or say which environment they came from.

## 3. Four hard rules

### Non-circular reference frame

Measure against something that does not depend on the thing under test. If you are testing how
`anchor` positions content, do not express results relative to a box derived from `anchor` — the
effect cancels out and everything looks correct. Pick an input you set directly.

Ask before every measurement: *if the mechanism under test were broken, would this number change?*
If not, the measurement is decorative.

### Calibrate the instrument before trusting it

A new measuring tool must pass both halves before its output counts:

- **Control**: something that should NOT change must measure identical across the two configurations.
- **Negative**: an effect that should be absent must read as absent.

Skipping this is how a confident, precise, wrong number gets acted on. If the first readings from a
new instrument are surprising, suspect the instrument before the system.

### An absence claim is worth what the probe covered

Both checks above guard a false positive. An absence claim -- "no hits", "not
present", "it never fires" -- fails the other way: a probe that cannot reach
the answer goes silent for the same reason a clean subject does. Run the
**positive control** first, against a case that must hit.

**A one-liner is an instrument** -- a `grep`, a `sed` range, a one-line
aggregation. None of them announces itself as a measuring tool, which is how
they go uncalibrated. The shapes that keep evading this are in
`references/instrument-design.md`.

### A test never seen red is not evidence

Before claiming a test proves a fix:

1. Predict the **direction and magnitude** of the failure without the fix.
2. Break the fix deliberately (revert the line, zero out the term, weaken the formula).
3. Confirm it fails **at the predicted magnitude**, not merely that it fails.
4. Restore, confirm green.

A test that goes red for a different reason than predicted means the model is still wrong.

### Environment is not the target

Numbers gathered in CI, headless browsers, containers, or emulators describe *that* environment.
Before promoting one into a durable claim, reproduce it where the users are, or label it. Prefer
assertions on **differences between configurations sharing one environment** over absolute values;
differences survive environment shifts, absolutes do not.

Reproducing is often cheaper than it looks. Check what reaches a real environment from here before
concluding you cannot: browser automation tools, a local app, a device, or simply asking the user to
paste one measurement. A single query in the real runtime can invert a conclusion that a whole
afternoon of headless measurement supported.

## 4. Recording the conclusion

Match durability to the evidence level, and say what the evidence was:

| Where | Needs | Never put here |
|---|---|---|
| Reply / commit body | L1+ | — |
| Code comment / JSDoc | L2+ for arithmetic, L3+ for engine behaviour | — |
| Project docs | L3+ | environment-specific absolutes without a label |
| Long-term memory / decision log | L3+ and the reasoning that survives | current API details |
| Shipped / distributed docs | L4+ | anything true only of this checkout or this machine |

## 5. When a later level contradicts an earlier conclusion

This is the expected outcome of climbing, not a failure. Handle it in this order:

1. **Stop propagating** — do not build further work on the retracted claim.
2. **Find where it already leaked**: replies are cheap, but code comments, docs, memory files and
   shipped artifacts all need correcting, and shipped ones matter most because someone downstream may
   act on them.
3. **Correct the claim and record the mechanism**, not just the correction — the reason the earlier
   level misled you is the reusable part.
4. **Keep a guard** so the retraction cannot silently reverse: a control test, a precondition test, or
   an explicit labelled caveat.

## Instrument how-to

Designing a probe that measures real runtime behaviour — shape, isolation, reference frame,
calibration cases, and the disposal traps — is in
[references/instrument-design.md](references/instrument-design.md).

That file is the judgment half. Mechanics belong to whichever project owns the runtime: if it
documents its own probe or harness pattern, follow that for how to wire one up, and this for whether
its readings can be believed.
