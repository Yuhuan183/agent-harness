# Harness review probes

Concrete, reproducible, read-only probes for the six review dimensions. Run from the repository root. Prefix every command with `rtk`; use raw output only when RTK hides evidence needed for the review.

## 1. Logic chain

```sh
rtk rg -n 'block|reject|refuse|prevent|enforce|guard' README.md docs main/claude main/codex --glob '*.md'
rtk rg -n 'sys\\.exit|parser\\.error|raise|returncode' main/claude/hooks main/claude/scripts main/codex/scripts
rtk rg -n 'request_source|origin_provider|fallback_hops|dispatch_id|rollout_id' main docs
```

For every prose guarantee, locate the field, gate, test, or sandbox boundary that carries it. If none exists, report it as policy only.

## 2. Flow

```sh
rtk rg -n 'READY|REVISE|CONFIRMED|REFUTED|INCONCLUSIVE' main/claude main/codex docs
rtk rg -n 'rollback|prerequisite|acceptance|owner|readiness-unit|slice' main/claude/plans docs
rtk rg -n 'dispatch|collect|QC|ledger' main/claude/skills main/codex/skills main/.agents/skills
```

Trace one direct task, one parallel dispatch, one provider fallback, one Plan revision, and one verifier flow end to end. Check stop conditions and identity handoff.

## 3. Language

```sh
rtk rg -n '后|软|们|信息|通过|优化|数据' README.md docs main --glob '*.md'
rtk rg -n '[，。；：]' main/claude/CLAUDE.contract.md main/codex/AGENTS.contract.md
rtk rg -n '(^|[^`])(python3|git|rg|find|sed|jq) ' README.md docs main --glob '*.md'
```

Taiwan-facing documents use Traditional Chinese and Taiwan terminology. Code, identifiers, commands, comments, and commit messages stay in English. Half-width punctuation is required only in agent-consumed resident contracts; human-facing documents may use normal Traditional Chinese punctuation.

## 4. Wording and context load

```sh
rtk wc -l main/claude/CLAUDE.contract.md main/codex/AGENTS.contract.md main/claude/agents/*.md main/claude/skills/*/SKILL.md
rtk scripts/prompt-census --check
rtk rg -n 'always|never|must|only|default' main/claude main/codex --glob '*.md' --glob '*.toml'
```

Identify duplicated resident rules, historical narrative in current guidance, vague terms without a shared definition, and strong wording unsupported by enforcement.

## 5. Module boundaries

```sh
rtk rg -n 'expanduser|HOME|CODEX_HOME|CLAUDE_HOME' main/.agents/skills/*/scripts main/claude/hooks main/claude/scripts main/codex/scripts
rtk git ls-files | rtk rg '(^|/)(settings\\.local|\\.skill-lock|telemetry|session|credentials)'
rtk awk -F '\\t' 'NF && $1 !~ /^#/ {print $1, $2, $3}' scripts/deployment-manifest.tsv
```

Separate repository policy, machine-local installer or service state, and current live state. Verify that deployable files live under `main/` and that dev-only material is absent from the manifest.

## 6. Verifiability

```sh
rtk /Users/zack/.local/bin/python3 -m unittest discover -s main/claude/tests -v
rtk main/claude/scripts/model-routing validate
rtk main/codex/scripts/model-routing validate
rtk main/claude/scripts/check-agent-pins
rtk main/claude/scripts/check-alias-generation
rtk scripts/sync.sh
```

Green static tests prove contract consistency, not runtime effectiveness. Name missing lifecycle, concurrency, provider, UI, network, or deployment evidence explicitly.

## Diff re-review

```sh
rtk git diff --check
rtk git diff --stat
rtk git diff -- README.md docs main .agents/skills/harness-review
rtk git status --short
```

Classify every original finding as resolved, accepted residual risk, or out of scope. Also inspect new contradictions introduced by the remediation itself.
