---
name: task-observer
description: Capture and review reusable skill-improvement observations. Invoke after skill-assisted work receives explicit dissatisfaction or a requested correction or rework (for example, 不滿意, 不符合, 不是我要的, 修正, 重做, unhappy, not what I asked, wrong, fix, redo, or rework), or when the user asks to record feedback, inspect the backlog, act on an observation, or review improvement opportunities. After handling the immediate correction, proactively ask once whether to record the feedback; write only with explicit consent. Do not invoke for ordinary task execution, background monitoring, or automatic skill updates.
---

# Task Observer

Capture qualitative skill feedback without turning every session into background
telemetry. Proposing feedback may be proactive, but persistence remains opt-in:
user authority is required before writing an observation or changing a skill.

This adaptation derives from Eoghan Henn's
[task-observer](https://github.com/rebelytics/one-skill-to-rule-them-all)
methodology. See `ATTRIBUTION.md` for licence and modification details.

## Boundaries

- Never activate merely because a task is multi-step or uses tools.
- Never create an observation unless the user explicitly agrees to record it.
- Never include secrets, credentials, personal data, or proprietary source text.
  Generalise the principle; use `internal` when project-specific context remains.
- Never edit, install, deploy, commit, publish, or delete a skill from an
  observation alone.
- Treat the Git source checkout as the authoritative skill source. Never edit a
  project-managed copy under `~/.agents/skills`, `~/.claude/skills`, or
  `~/.codex/skills`; deployment replaces it. The ledger is machine-local
  evidence, not a source tree or staging area.
- Keep dispatch-quality metrics in `experience-ledger`; this skill records
  qualitative workflow and skill-design feedback only.

## Propose feedback after friction

1. Handle the requested correction or rework first. Do not interrupt recovery
   with a feedback question.
2. Treat explicit dissatisfaction or a requested correction after skill-assisted
   work as a signal. Chinese and English examples in the description are
   illustrative, not an exact keyword match; require context linking the
   friction to a reusable skill or workflow behaviour.
3. After presenting the corrected outcome, ask once in the user's language:
   - Chinese: `這次調整可能反映 skill 或工作流程可以改進。要把它記錄成改善觀察嗎？`
   - English: `This adjustment may reveal a reusable skill or workflow improvement. Should I record it as an observation?`
4. If the user agrees, record one bounded observation. Combine repeated
   corrections from the same incident instead of asking or logging repeatedly.
5. If the user declines or ignores the question, do not write anything and do
   not ask again for the same incident.

## Record an observation

1. Confirm the user explicitly agreed to persist the observation.
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
`main/.agents/skills/task-observer/scripts/observation-log` before deployment.
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
Resolve the target before proposing or applying a change:

```bash
~/.agents/skills/task-observer/scripts/observation-log target \
  --skill "<skill>" --json
```

For a project-managed skill, use only the returned `source_path`; the command
fails closed when it cannot verify the source checkout. For
`local-or-third-party`, establish ownership separately and do not treat the
installed path as editable merely because it exists. Use `skill-creator` for
the actual authoring workflow. Present the proposed scope and obtain explicit
approval before modifying the resolved source.

## Storage

The default ledger is
`~/.agents/telemetry/skill-observations.jsonl`. Override it for tests or a
deliberately separate machine-local ledger with `AGENT_SKILL_OBSERVATIONS`.
The script uses append-only schema-v1 events, UUID identifiers, an exclusive
file lock for writes, and a shared lock for reads.
