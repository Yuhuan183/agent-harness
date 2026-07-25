# Bridge dispatch liveness

A Codex bridge dispatch outlives the call that started it. The Claude-side
launcher is a thin forwarder in its own process; the Codex job is not its
child. Kill the forwarder — a Bash timeout, a cancelled tool call, a crashed
session — and the job keeps running, keeps its sandbox, and keeps whatever
write access its role was given.

Every rule below follows from that one fact.

## The rule

**A dead launcher is not a dead dispatch.** Never infer job state from
launcher state. Before relaunching, resuming, or writing off any bridge
dispatch, ask the companion what is actually alive:

```bash
~/.codex/scripts/bridge-jobs --workspace "$PWD" --duplicates
```

- exit 0 — answered, no twins
- exit 1 — twins exist, listed with the `/codex:cancel` line for each
- exit 2 — **could not answer**; this is not "nothing is running", and nothing
  may be relaunched on the strength of it

Liveness is decided by asking the OS about the job's recorded pid, not by the
`status` field. Status outlives the process: a job killed abruptly keeps
`status: running` in its state file indefinitely. Those show up separately as
"died without updating their state" — not a duplicate risk, but the difference
between a dispatch still working and one that gave you nothing. A record whose
pid cannot be checked counts as live, because for a duplicate guard
over-reporting is the safe direction.

## Why it is load-bearing

`baton-dispatch` requires one owner per writable artifact. Ownership attaches
to a *live job*, not to a launch attempt, so a relaunch that leaves the first
job running hands the same artifacts to two writers — the single-owner rule is
broken without anyone choosing to break it, and neither agent can see the
other.

This is not hypothetical. On 2026-07-26 a forwarder hit the two-minute Bash
cap, read the timeout as failure, and relaunched the same full-repo review
prompt. Both Codex jobs ran against one workspace for 4m49s until the older
was cancelled by hand. Both happened to be read-only, which is a property of
the role that was dispatched, not of any mechanism — the same sequence with an
`executor` would have had two agents editing one tree.

## Procedure

**Launcher died, job state unknown.** Run the check above. If a job for this
prompt is live, do not relaunch: it is still your dispatch, and it will finish.
Poll it (`node <companion>/scripts/codex-companion.mjs status <job-id>`) or
wait on its state file. Relaunch only after the check reports no live twin.

Poll on the companion's job id (`task-<slug>`), not the rescue subagent's own
task id — they are different id spaces, and `status` on the wrong one answers
"No job found", which is indistinguishable from "not finished yet".

**Reported dead.** A job listed as died-without-updating produced nothing;
relaunching is correct, and there is no twin to cancel. Waiting on its state
file would wait forever, since nothing will ever rewrite it.

**Twins already exist.** Keep exactly one and cancel the rest. Keep the one
whose route you can attest — `route_source: rollout-verified` comes from the
job's own Codex rollout, so the surviving job's `threadId` is what makes its
ledger record evidence rather than a claim. Log only the survivor; a cancelled
twin produced no accepted outcome and must not enter a cohort.

**Cancelling.** `/codex:cancel <job-id>`, or the companion's `cancel`
subcommand. Cancellation is recorded in the job state, so a later check sees
`cancelled`, not a phantom live job.

## What to re-check when the bridge changes

The companion owns the job-state layout this depends on. After a plugin
upgrade, confirm:

- job records still carry `status`, `sessionId`, `workspaceRoot`, `summary`,
  and `startedAt` — `bridge-jobs` groups twins on the last three and filters on
  the first
- the live-status vocabulary still fits `running | queued | starting`
- the rollout still records `thread_settings_applied` with `model` and
  `reasoning_effort`, which is what makes a bridge route attestable at all

`main/claude/tests/test_mechanisms.py::BridgeJobLivenessTests` pins the
duplicate-detection behaviour; `test_ledger.py::BridgeRouteEvidenceTests` pins
the route-evidence path.
