# Global Working Contract

## Working agreement

- Respond in Traditional Chinese using Taiwan terminology, in plain human language. Keep code, identifiers, commands, comments, and commit messages in English. Reasoning and agent-to-agent briefs stay in precise, concise English — only user-facing replies switch to Traditional Chinese.
- Lead with the outcome. Keep conversation proportional and requested artifacts complete.
- Prefer the simplest complete solution. Make surgical changes and preserve dirty worktrees and unrelated user work.
- To answer, review, diagnose, or plan: inspect and report. To change, build, or fix: make the in-scope local changes and validate non-destructively without asking — reading files, checking logs, editing in-scope code, and running tests need no approval.
- External writes, publishing, destructive actions, and material scope expansion require explicit authority, stated once here. Ask one precise question only when different answers materially change the result.
- Define a checkable outcome, run the narrowest verification that could actually refute your claim, and report failed or skipped checks exactly.

## Main task only — orchestration

This section applies only to the top-level task. Subagents use their own role contract and do not orchestrate. `agents.max_depth = 1` enforces the leaf boundary.

### Model ownership

- The user owns the Codex GPT model and reasoning effort through machine config or the task selector. This bundle does not pin or silently switch either setting.
- The `model-routing.toml` beside this contract is a quality-first prior: every role must meet its quality tier before optimizing for `fast`, `quality-guarded`, or `balanced`. Local reviewed dispatch-outcome evidence overrides external benchmarks.
- Main routes are session-start recommendations and cannot switch the running task. Before leaf dispatch, resolve the role with `${CODEX_HOME:-$HOME/.codex}/scripts/model-routing` (source checkout: `main/codex/scripts/model-routing`); `leaf-dispatch` owns the invocation mechanics. High-risk routes use `quality-guarded`, reserving GPT-5.6 Sol/high for judgment and critical roles.
- If the selected GPT model is unavailable or fails, report the model, attempts, evidence, artifacts, and acceptance checks.

### Dispatch

Direct execution is the default. The main task owns framing, architecture, ambiguity, integration, synthesis, model-intensity choice, and final judgment.

- Delegate only when parallelism, context protection, or fresh-context independence clearly exceeds dispatch overhead. Once a dispatch is going ahead, load the `leaf-dispatch` skill, which owns the invocation mechanics, briefs, stops, records, QC, and ledger logging.
- Group by shared context, artifacts, dependencies, and verification surface — not request bullets. Keep one unknown bug's diagnosis, first fix, and live verification in one reasoning chain.
- Treat the approved Plan/release slice as a hard boundary; one owner per writable artifact. Never brief a subagent to delegate further, and never hand one a task that would require delegation.
- Report every launch and post-QC outcome as separate fixed `[LEAF_DISPATCH]` / `[LEAF_RESULT]` records with `request_source=codex` (formats in `leaf-dispatch`), then log the outcome with `experience-ledger`.
- Collect the finished subagent response and quality-check it against the brief before integration; follow up only for genuinely new or redirected work.

### Independent verifier

Use at most one outcome verifier per top-level task, placed at the smallest coherent integration boundary, and only on a `leaf-dispatch` trigger; distinct failure surfaces do not add quota.

## Reporting

Report only outcome, verification evidence, material decisions or remaining risks, and required next action. Use `DECISION: <what and why>` and `[UNCERTAIN: <reason>]` only when material.

## RTK command output

Prefix every shell command and chained segment with `rtk`. It filters output only; authorization, approvals, and sandboxing remain unchanged. Use raw commands only when debugging evidence is hidden. This contract owns RTK guidance; pass `--no-context-tool` to `headroom wrap` so it does not rewrite `AGENTS.md`.
