# Codex / ChatGPT Distillation

## Result

This directory is the reviewed deployment source for Codex and ChatGPT, not automatic deployment. It carries outcome-first communication, direct-first orchestration, seven leaf-role contracts, quality-first model routing, experience-based provider revision, and risk-triggered independent verification.

Codex receives the full global contract and registered leaf agents. ChatGPT chat receives only response preferences because it does not expose this repository's agent runtime.

## Ownership and execution surfaces

- Git is the cross-machine source of truth. GPT model/effort, auth, credentials, sessions, MCP/plugin paths, quotas, and local telemetry remain machine state.
- Main owns framing, architecture, ambiguity, dispatch decisions, integration, synthesis, and final judgment.
- Leaf roles receive self-contained contracts, never orchestrate, and are bounded by `agents.max_depth = 1`.
- Codex native and Claude→Codex bridge routes are resolved per dispatch from `model-routing.toml`; main routes are session-start recommendations and cannot switch a running task.
- Claude named roles use a separate deployment preset. Changing a Codex route never changes Claude frontmatter pins or either main model.

## Routing evidence

Artificial Analysis v4.1 values are dated priors, not local coding-agent success rates. Every role must pass its quality floor before optimizing for `balanced`, `fast`, or `quality_guarded`; there is no economy profile that lowers quality.

Local reviewed outcomes supersede external priors once the executable `revision_policy` reaches comparable evidence: same role and task class, 90-day window, 45-day half-life, at least 10 samples per route cell, and P(win) at least 0.90. Both provider files must carry exactly the same policy or reporting/revision stops.

Experience schema v3 records `request_source` (`codex`, `claude-code`, or `claude-code-plugin-codex`), profile/model/effort, dispatch/rollout identity, outcome, time, and token coverage. Reports never compare total-token data with output-only data and exclude smoke/other cohorts from decisions.

## Verification and deployment boundary

Delegation requires an observable outcome, measurable benefit over direct work, exclusive artifact ownership, and a main-owned integration check. Independent verification is conditional on security/trust boundaries, money, destructive data, migrations, concurrency, public APIs, cross-repo compatibility, adversarial acceptance, conflicting evidence, failed reproduction, or explicit user request.

`scripts/sync.sh` runs preflight before writes, backs up managed targets, preserves machine-owned Codex config, and verifies post-apply parity. Claude preset activation is performed in the source checkout, reviewed, then deployed; editing only the installed copy is machine-local drift.

## Artifact map

| Source | Target / purpose |
|---|---|
| `main/.codex/AGENTS.contract.md` | `$CODEX_HOME/AGENTS.md` |
| `main/.codex/config.merge.toml` | Manual merge into `$CODEX_HOME/config.toml` |
| `main/.codex/agents/*.toml` | Registered Codex leaf roles |
| `main/.codex/model-routing.toml`, `main/.codex/scripts/` | Native and Claude-bridge per-dispatch routing |
| `main/.agents/skills/experience-ledger/` | Shared machine-local outcome analysis |
| `main/.codex/prompts/custom-instructions.md` | ChatGPT Personalization only |

Use `DEPLOY.md`. A successful login proves authentication only; it does not prove contract loading, routing, leaf overrides, or source/target parity.
