# Harness review probes

Use this file as a menu of read-only discovery and falsification probes. Run
from the repository root. Prefix every shell command and chained segment with
`rtk`; use raw output only when filtering hides evidence needed for a claim.
Do not run every command mechanically.

## Contents

- Establish scope
- Inventory and authority
- Contract enforcement and routing
- Flow, state, and handoff closure
- Language and wording
- Modularity, sharing, and deployment ownership
- Fixed context overhead
- Validation layers
- Remediation re-review

## Establish scope

```sh
rtk git status --short
rtk git branch --show-current
rtk git rev-parse HEAD
rtk git diff --stat
rtk git diff --check
rtk git diff -- <reviewed paths>
```

For a historical range, replace the final command with the exact base and
head. Read changed files whole after inspecting the diff.

## Inventory and authority

```sh
rtk rg --files README.md docs main scripts .agents/skills/harness-review
rtk find main -maxdepth 5 -type f
rtk awk -F '\t' 'NF && $1 !~ /^#/ {print $1, $2, $3}' scripts/deployment-manifest.tsv
rtk rg -n 'must|never|always|only|default|block|reject|enforce' README.md docs main --glob '*.md' --glob '*.toml'
```

Classify each result as repository policy, deployable source, machine-local
state, or live state before drawing conclusions.

## Contract enforcement and routing

```sh
rtk rg -n 'block|reject|refuse|prevent|enforce|guard|fail.closed|fail.open' README.md docs main --glob '*.md' --glob '*.py' --glob '*.sh' --glob '*.toml'
rtk rg -n 'sys\.exit|parser\.error|raise|returncode|exit [1-9]' main scripts
rtk rg -n 'request_source|origin_provider|fallback_hops|dispatch_id|rollout_id' main docs
rtk rg -n 'provider|model|priority|fallback|quota|unavailable' main/claude main/codex
```

For each strong policy verb, locate the carrier, executable gate, failure
result, and regression test. Search is only the start of the trace.

## Flow, state, and handoff closure

```sh
rtk rg -n 'READY|REVISE|CONFIRMED|REFUTED|INCONCLUSIVE|blocked|complete' main docs
rtk rg -n 'rollback|prerequisite|acceptance|owner|readiness|stop.condition|handoff' main docs
rtk rg -n 'dispatch|collect|quality.check|verifier|ledger|approval' main docs
rtk rg -n 'retry|cancel|timeout|concurrent|stale|idempot' main scripts
```

Trace at least one direct task, one dispatched task, one fallback or
unavailability path, one approval boundary, and one verifier flow when each is
present in scope. Identify the owner and stop condition at every edge.

## Language and wording

```sh
rtk rg -n '后|软件|信息|通过|优化|数据' README.md docs main --glob '*.md'
rtk rg -n '[，。；：]' main/claude/CLAUDE.contract.md main/codex/AGENTS.contract.md
rtk rg -n '\b[A-Z]{2,}\b' README.md docs main --glob '*.md'
rtk rg -n 'exactly one|at most one|one or more|stack|single|唯一|至多|至少' README.md docs main --glob '*.md'
```

Classify the audience first. Runtime agent text, code, identifiers, commands,
comments, and commit messages use English. Human-facing prose uses Traditional
Chinese with Taiwan terminology. Acronym and cardinality hits are candidates,
not automatic defects.

## Modularity, sharing, and deployment ownership

```sh
rtk rg -n 'expanduser|HOME|CODEX_HOME|CLAUDE_HOME' main scripts
rtk git ls-files | rtk rg '(^|/)(settings\.local|\.skill-lock|telemetry|session|credentials)'
rtk rg -n 'CLAUDE\.contract|AGENTS\.contract|deployment-manifest|sync\.sh' main scripts docs
rtk scripts/sync.sh
```

Confirm that deployable content originates under `main/`, dev-only root
content is absent from the manifest, preflight does not rely on the installed
copy, and mirrored contracts have an explicit source or parity gate. Treat
`scripts/sync.sh` as a dry-run unless the user separately authorizes apply.

## Fixed context overhead

```sh
rtk wc -l -w -c main/claude/CLAUDE.contract.md main/codex/AGENTS.contract.md
rtk wc -l -w -c main/claude/agents/*.md main/codex/agents/*.toml
rtk main/.agents/scripts/python3-run scripts/prompt-surface-census.py --check docs/research/prompt-surface-census.json
rtk rg -n 'load|resident|always.loaded|budget|limit|cache|probe' README.md docs main
```

Locate the actual load point before assigning cost. Measure the unit named by
the budget and test whether long lines, generated duplication, CJK text, or
conditional content can evade it.

## Validation layers

```sh
rtk main/.agents/scripts/python3-run -m unittest discover -s main/claude/tests -v
rtk main/claude/scripts/model-routing validate
rtk main/codex/scripts/model-routing validate
rtk main/claude/scripts/model-routing check-pins
rtk main/claude/scripts/model-routing check-aliases
rtk scripts/sync.sh
```

Run the narrowest relevant checks first. Record what each command is capable of
proving, not only whether it passed. Recheck `git status --short` afterward and
remove temporary review artifacts.

## Remediation re-review

```sh
rtk git diff --check
rtk git diff --stat
rtk git diff -- README.md docs main scripts .agents/skills/harness-review
rtk git status --short
```

For every prior finding, classify `resolved`, `partially resolved`,
`accepted risk`, or `out of scope`. Then inspect sibling invalid inputs,
changed budget units, generated copies, exact-string tests, deployment
semantics, and rollback paths for second-order defects.
