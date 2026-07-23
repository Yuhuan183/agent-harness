---
name: task-observer
description: Capture and review reusable skill-improvement observations only when the user explicitly asks to record an observation, inspect the observation backlog, act on a named observation, or review skill-improvement opportunities. Do not invoke for ordinary task execution, implicit background monitoring, or automatic skill updates.
---

# Task Observer

Capture qualitative skill feedback without turning every session into background
telemetry. This is an opt-in workflow: user authority is required before writing
an observation or changing a skill.

This adaptation derives from Eoghan Henn's
[task-observer](https://github.com/rebelytics/one-skill-to-rule-them-all)
methodology. See `ATTRIBUTION.md` for licence and modification details.

## Boundaries

- Never activate merely because a task is multi-step or uses tools.
- Never create an observation unless the user explicitly asks to record one.
- Never include secrets, credentials, personal data, or proprietary source text.
  Generalise the principle; use `internal` when project-specific context remains.
- Never edit, install, deploy, commit, publish, or delete a skill from an
  observation alone.
- Treat the Git source checkout as the authoritative skill source. The ledger is
  machine-local evidence, not a source tree or staging area.
- Keep dispatch-quality metrics in `experience-ledger`; this skill records
  qualitative workflow and skill-design feedback only.

## Record an observation

1. Confirm the user asked to persist the observation.
2. Reduce it to:
   - `skill`: an existing skill name, `new-skill:<name>`, or `all-skills`
   - `area`: the workflow phase or section
   - `issue`: concrete evidence that will remain understandable later
   - `suggested improvement`: one bounded change
   - `principle`: the reusable lesson without sensitive details
   - `type`: `open-source` or `internal`
3. Run:

```bash
~/.agents/skills/task-observer/scripts/observation-log add \
  --skill "<skill>" \
  --area "<area>" \
  --issue "<issue>" \
  --improvement "<bounded change>" \
  --principle "<reusable lesson>" \
  --type "<open-source|internal>"
```

Use the source-checkout path
`.agents/skills/task-observer/scripts/observation-log` before deployment.
Add `--session-context` or `--reference-file` only when needed. The script
returns the immutable observation ID; cite that ID exactly.

## Inspect or resolve observations

These commands are read-only:

```bash
~/.agents/skills/task-observer/scripts/observation-log list --status open
~/.agents/skills/task-observer/scripts/observation-log review
```

Use `--json` with `list` when structured data is needed. Listing a missing
ledger must not create it.

Resolve an observation only after the user approves the disposition:

```bash
~/.agents/skills/task-observer/scripts/observation-log resolve \
  --id "<observation-id>" \
  --resolution "<actioned|declined>" \
  --note "<what changed or why declined>"
```

Resolution appends an event; it never rewrites or archives prior evidence.

## Review and change skills

For backlog review or any skill change, read `references/review.md` first.
Use `skill-creator` for the actual skill authoring workflow. Present the proposed
scope and obtain explicit approval before modifying the source checkout.

## Storage

The default ledger is
`~/.agents/telemetry/skill-observations.jsonl`. Override it for tests or a
deliberately separate machine-local ledger with `AGENT_SKILL_OBSERVATIONS`.
The script uses append-only schema-v1 events, UUID identifiers, an exclusive
file lock for writes, and a shared lock for reads.
