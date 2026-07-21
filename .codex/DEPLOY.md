# Codex / ChatGPT Deployment

This bundle never auto-deploys. Git distributes source; each machine requires backup, merge, validation, and a new task.

## One-shot Codex command

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
codex --ask-for-approval on-request --sandbox workspace-write -C "$REPO_ROOT" \
  "Read .codex/DEPLOY.md completely. Deploy its Codex bundle with backups and merge-only config changes; preserve machine state, show material conflicts, run every verification, and report the backup path."
```

Deployment writes outside the repository. Keep approval enabled; never use a sandbox-bypass flag.

## Codex deployment contract

1. Resolve `CODEX_HOME` (default `$HOME/.codex`) and show source/target paths.
2. Back up every changed target under `$CODEX_HOME/backups/<timestamp>/`. Never copy credentials, tokens, sessions, or secrets into the repo or output.
3. Install `codex/AGENTS.md`. Diff an existing non-empty file; preserve unrelated guidance and stop on material conflict. Check higher-precedence `AGENTS.override.md`.
4. Merge `codex/config.merge.toml`; never replace `config.toml`. Preserve GPT model/effort, auth, MCP, plugins, desktop, project trust, hooks, notifications, and unrelated keys.
5. Install every `codex/agents/*.toml`, `codex/skills/`, `codex/model-routing.toml`, and `codex/scripts/model-routing`; back up same-name conflicts.
6. Do not add or change Headroom routing, base URL, MCP, hook, or lifecycle state.
7. Verify `AGENTS.md` sections occur once; require source/target equality for every agent file, skill, routing file, and routing script; parse TOML; run `scripts/model-routing validate`; resolve native and `--surface claude-bridge` routes for all profiles, confirming current support routes never select Luna; assert `max_threads = 4`, `max_depth = 1`, and every registered agent's `config_file` exists.
8. Run `codex --strict-config --version`.
9. Start a new read-only task and confirm outcome-first output, direct-first routing, main/leaf separation, and model-selection ownership. Spawn a verifier smoke test only with explicit user authorization.
10. Report outcome, backup path, checks, conflicts/risks, and restart requirement.

Codex CLI, App, and IDE extension share these files only when they use the same `CODEX_HOME`. Existing tasks do not reliably hot-reload the instruction chain.

## ChatGPT Personalization

Manually merge `chatgpt/custom-instructions.md` in **Settings > Personalization > Custom instructions**. Test in new chats: ordinary response, `tldr:`, and `deep:`. Do not paste the shorter ChatGPT prompt into Codex App after deploying the full Codex contract.

## Sync boundary

| Artifact | Account-synced? |
|---|---:|
| `$CODEX_HOME/AGENTS.md`, `config.toml`, `agents/` | No |
| `$HOME/.agents/skills/` | No |
| Credentials and login | Authentication only |
| ChatGPT custom instructions | Account/workspace personalization where supported |

Never sync credentials, session databases, absolute machine paths, or whole machine config through this repository.

Official references: [Codex environment variables](https://learn.chatgpt.com/docs/config-file/environment-variables), [configuration](https://learn.chatgpt.com/docs/config-file/config-basic), [`AGENTS.md`](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [ChatGPT personalization](https://learn.chatgpt.com/docs/personalize).
