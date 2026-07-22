# Probe commands and known traps

Concrete, reproducible probes per dimension. All read-only.

## Inventory (run first)

```bash
# Resident/doc sizes vs budgets (word budgets live in .claude/tests/test_contracts.py)
wc -l .claude/CLAUDE.contract.md .codex/AGENTS.contract.md \
      .claude/agents/*.md .claude/skills/*/SKILL.md

# Chinese-content ratio per file (zh lines / total) — grounds dimension 3
for f in .claude/CLAUDE.contract.md .codex/AGENTS.contract.md \
         .claude/agents/*.md .claude/skills/*/SKILL.md README.md docs/*.md; do
  echo "$(grep -c '[一-龥]' "$f" 2>/dev/null || echo 0)/$(wc -l < "$f") $f"
done
```

## Dimension 1 — logic chain

```bash
# Enforcement verbs that must map to a real mechanism
rg -in 'block|reject|refuse|prevent|enforce|guard' --type md .claude .codex README.md

# For each hit inside a hook/script claim: verify the mechanism can actually fail
rg -n 'sys.exit|parser.error|raise|returncode' .claude/hooks/*.py .claude/scripts/* .codex/scripts/*
# A "guard" with no non-zero exit path is a warning, not a guard.

# Bootstrap self-dependency: repo tooling that resolves $HOME-deployed state
rg -n 'expanduser|HOME' .agents/skills/*/scripts/* .claude/hooks/*.py | rg -v 'AGENT_[A-Z_]+'
# Rule: repo-internal callers must be overridable by env and default sanely inside the checkout.
```

Cross-file contradiction hunt: for each routing question (fallback target,
effort cap, mandatory-skill trigger), list every file answering it and diff the
answers. Known past pair: SKILL routing prose vs `model-routing.toml` presets.

## Dimension 2 — flow

For every prose invariant, name the field or record that carries it
(`origin_provider`? `fallback_hops`? approval step in the loop diagram?).
No field → finding. Check README mermaid diagrams end in a closed loop, not at
"suggestion".

## Dimension 3 — language

```bash
# PRC variants in zh-TW prose (extend list as found)
rg -n '后|软|们|信息|通过|优化|数据' --type md . docs
# Runtime (agent-consumed) files should be English: agents/, skills consumed at
# dispatch time, script comments. Human docs (README, docs/) stay zh-TW.
```

## Dimension 4 — wording

Term census: for each load-bearing term (`source`, `verifier`, `fast`,
`accepted`, acronyms like `CP-first`), `rg` all uses and check one definition,
one meaning. Flag: undefined acronyms, cardinality stated differently in two
places, claims a validator does not actually check.

## Dimension 5 — modularity

```bash
# Deployment surface: everything deployed should be read by some runtime
cat scripts/deployment-manifest.tsv
# Twin parity: diff role semantics, not just registration
diff <(sed -n '/^---$/,$p' .claude/agents/verifier.md) <(cat .codex/agents/verifier.toml)
# Ownership: personal prefs (theme/tui/notifications) must not sit in tracked settings
jq 'keys' .claude/settings.json
```

## Dimension 6 — overhead

Budgets: check the test enforces a unit that cannot be gamed (words/tokens, not
lines). Hooks: list per-session work (`settings.json` hooks) and ask what a
cache would eliminate. Compare Claude vs Codex resident size for the same
policy content.

## Bridge (dual-provider pass)

- Resolve route first: `~/.codex/scripts/model-routing resolve --surface
  claude-bridge --priority quality-guarded --role verifier`; pass model/effort
  explicitly; prepend the role contract; state read-only prohibitions
  explicitly (bridge is write-capable by default).
- The rescue subagent is a one-shot forwarder: it cannot poll. The Codex job
  keeps running after the subagent returns "Task started". Poll from main:
  `node ~/.claude/plugins/cache/openai-codex/codex/<ver>/scripts/codex-companion.mjs
  status <task-id>`, then `result <task-id>`.
- Poll trap: status output contains progress lines like "Command completed:" —
  match the job's own status line (`^- <task-id> \| running`), never the bare
  word "completed".
- `result` on a still-running job returns "No job found" — that means not
  finished, not lost.
- Ledger: the hook-staged pending stub has no route fields for bridge
  dispatches; pass `--profile/--model/--effort` (and `--dispatch-id` when
  multiple completions are pending) explicitly to `experience-log`.

## Remediation-round probes (second-order defects)

```bash
# Validation completeness: for every new reject rule, probe the sibling shapes
# (negative, zero, missing-companion-field, equal-to-self) — not just the one
# the finding named.
# Budget recalibration: after changing the budget unit, re-measure every
# budgeted file in the NEW unit before touching the numbers.
# CJK budget check — split() counts a zh sentence as 1; word_count() must not:
python3 -c "print(len('常駐指令檔縮到只剩模型推不出來的東西'.split()))"   # 1 == gameable
# Punctuation policy (zh-TW full-width) — should return nothing:
rg -n '[一-鿿][,;:]' --glob '*.md' README.md docs .claude .agents
```

## Route/latency calibration (observed 2026-07-22)

- Full-repo GPT pass, Sol/high, quality-guarded: ~6–10 min wall-clock,
  ~20 tool turns, ~3.3M input tokens (94% cached), ~21k output (13.5k
  reasoning). This is inherent to adversarial full-repo review, not a hang.
- Re-review of a remediation: prefer `priority=balanced` and `scope=diff` —
  roughly half the reasoning cost; keep quality-guarded for first passes and
  security-adjacent scopes. Log both kinds in the ledger so the choice becomes
  evidence-driven.
