# Attribution and licence

Portions of the methodology and terminology in this skill are adapted from
**Task Observer — Continuous Skill Discovery & Improvement**, created by
**Eoghan Henn / [rebelytics.com](https://rebelytics.com)**:

https://github.com/rebelytics/one-skill-to-rule-them-all

Reviewed upstream revision:

- Version: `v2.0.0`
- Commit: [`281f13466cd3a73e9ebc9d210907748e1941a3dd`](https://github.com/rebelytics/one-skill-to-rule-them-all/commit/281f13466cd3a73e9ebc9d210907748e1941a3dd)

The upstream work is licensed under the
[Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/).

This adaptation changes the upstream design by making activation and writes
explicitly opt-in, replacing the mutable numbered Markdown log with an
append-only locked JSONL event ledger, treating the Git checkout as the skill
source of truth, and prohibiting automatic edits, deployment, commits, deletion,
or scheduled application.

The rest of the `agent-harness` repository remains under its existing licence;
this notice applies to the adapted task-observer material.
