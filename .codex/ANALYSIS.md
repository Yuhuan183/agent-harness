# Codex / ChatGPT Distillation

## Result

The bundle carries only Codex/ChatGPT contracts: outcome-first communication, minimal scope, verified completion, direct-first dispatch, main-task judgment, approved-scope boundaries, and risk-triggered independent verification.

Codex receives a global contract, seven custom leaf agents mirroring the Claude roles, and `max_depth = 1`; ChatGPT receives response preferences only.

## Source and ownership

- Reviewed source: current harness contract as of 2026-07-17, including Baton scope fix `0ab4d2e` and finished-task result collection.
- This directory is deployment source, not automatic deployment.
- Git is the cross-machine source of truth. GPT model/effort, auth, MCP/plugin paths, and credentials remain machine state.

| Concern | Codex target | ChatGPT target |
|---|---|---|
| Working agreement | `codex/AGENTS.contract.md` | `chatgpt/custom-instructions.md` |
| Main-only orchestration | `codex/AGENTS.contract.md` main-task section | Not ported |
| Leaf execution | Seven custom leaf agents (`agents/*.toml`) | Not available |
| Optional compression | `codex/skills/headroom-protocol` | Not ported |
| GPT model/effort | Machine config or task selector | Product selector |

## Main and leaf separation

Main tasks own framing, architecture, ambiguity, model-intensity choice, integration, synthesis, and final judgment. Leaf roles receive self-contained contracts and never read orchestration docs or spawn more agents.

Codex enforces this with `agents.max_depth = 1`. The custom verifier is sandboxed read-only.

## Dispatch and verification

Delegation requires an observable outcome, measurable benefit over direct work, independent workstreams, exclusive artifact owners, and an integration/final-verification owner. Approved scope is a hard boundary. Finished subagent output is collected directly and is not relaunched for repetition.

The verifier is conditional: security/trust boundaries, money/destructive data, migrations/concurrency/public APIs/cross-repo compatibility, non-mechanical integration claims, adversarial state behavior, conflicting evidence, failed reproduction, or explicit user request. Docs-only, trivial config, decisive mechanical checks, and low-risk direct work stay in main.

## Model ownership

The bundle does not pin or silently switch the GPT model or reasoning effort. Machine configuration and the task selector remain authoritative. A model failure is reported with attempts, evidence, artifacts, and acceptance checks; further model selection waits for user direction.

## Deliberately not ported

- Non-Codex role names, frontmatter model routing, platform-specific hooks, audit, statusline, RTK hook, or rescue commands.
- Durable Headroom routing, base URLs, GPT runtime config, binary paths, or lifecycle hooks.
- Usage telemetry assumptions, subscription-quota inference, or retired observer plugins.

## Files and smoke tests

| File | Target |
|---|---|
| `codex/AGENTS.contract.md` | `$CODEX_HOME/AGENTS.md` |
| `codex/config.merge.toml` | Merge into `$CODEX_HOME/config.toml` |
| `codex/agents/verifier.toml` | `$CODEX_HOME/agents/verifier.toml` |
| `codex/skills/headroom-protocol/` | `$HOME/.agents/skills/headroom-protocol/` |
| `chatgpt/custom-instructions.md` | ChatGPT Personalization |

Use `DEPLOY.md`. Verify source/target equality where required, TOML parsing, `max_depth = 1`, global instruction loading in a new task, conditional verifier behavior, and manual ChatGPT prompt behavior. Do not infer deployment from account login.
