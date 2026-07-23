# Observation Review

Load this file before reviewing the backlog, proposing skill changes, or
resolving observations.

## Resolve target ownership

Before proposing or applying a skill change, run:

```bash
observation-log target --skill "<skill>" --json
```

- `project-managed`: edit only the returned `source_path`, which must resolve to
  `<checkout>/main/.agents/skills/<skill>`. Never edit the deployed HOME copy;
  the next managed merge replaces it.
- `local-or-third-party`: `source_verified` is false and `source_path` is null.
  Determine whether the installed path is a personal source, installer output,
  plugin cache, or another project's deployment, then obtain authority for that
  actual source.
- Resolution failure is a stop condition. Supply `--checkout <path>` or
  `AGENT_HARNESS_CHECKOUT` after locating the checkout; never fall back to the
  deployed copy.

## Review queue

1. Run `observation-log list --status open --json`.
2. Resolve every target's ownership and include its authoritative source path.
   Reconstruct scope from that source, not from deployed HOME copies, prior
   drafts, or observation wording alone.
3. Group observations by target skill. Keep these categories distinct:
   - improvement to an existing skill
   - simplification or removal candidate
   - new skill candidate
   - cross-cutting principle (`all-skills`)
4. Revalidate each observation:
   - Is the evidence still true in the current source?
   - Does it generalise beyond one accidental failure?
   - Is a skill the right layer, or should the behaviour be a script, hook,
     test, role contract, or documentation?
   - Does it overlap existing memory, telemetry, or another skill?
5. Present a compact proposal with observation IDs, affected files, intended
   behaviour, verification, and anything deliberately excluded.

Do not apply changes until the user explicitly approves the proposal.

## Applying an approved observation

1. Load `skill-creator`.
2. Re-run `observation-log target`; read the returned source skill and every
   directly referenced resource required by the change.
3. Make the smallest source-checkout change that implements the approved
   behaviour. Preserve unrelated user work.
4. Keep fragile operations in deterministic scripts. Keep SKILL.md limited to
   routing and essential workflow.
5. Preserve third-party attribution and licence notices.
6. Run:
   - the changed skill's focused tests
   - `quick_validate.py` for the skill directory
   - the harness contract suite when deployment, symlinks, or shared
     instructions changed
   - `git diff --check`
7. Present the diff and verification evidence. Do not deploy, commit, push, or
   publish unless separately authorised.
8. Only after the change is accepted, append an `actioned` resolution event.
   If the user rejects the proposal, append `declined` with the reason.

## Cross-cutting principles

An `all-skills` observation is a review candidate, not an instruction to rewrite
every skill. Ask whether propagation is:

- immediate: address the approved, enumerated skills now
- opportunistic: apply when each skill is next changed

Keep the decision in the resolution note. Do not maintain a second mutable
principles file; the event ledger remains the evidence source.

## New skill candidates

Do not create a new skill during backlog review without explicit approval of its
name, triggers, scope, writable surfaces, and acceptance checks. A repeated
workflow is evidence for a skill only when it cannot be handled more simply by
existing instructions, scripts, or ordinary model capability.
