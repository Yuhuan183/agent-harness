# Attribution and licence

Portions of the methodology and terminology in this skill are adapted from
**Task Observer — Continuous Skill Discovery & Improvement**, created by
**Eoghan Henn / [rebelytics.com](https://rebelytics.com)**:

https://github.com/rebelytics/one-skill-to-rule-them-all

Reviewed upstream revision:

- Version: `v3.1.0`
- Commit: [`f4a95a180404bd4de35365da66849a243e3d07be`](https://github.com/rebelytics/one-skill-to-rule-them-all/commit/f4a95a180404bd4de35365da66849a243e3d07be)

Advanced from `v3.0.0` (`9d1491b895c4f8f04f04977f74faad0f342c8b0c`) on 2026-09-05,
after every rule in the 3.1 changes was classified and each disposition checked
against this tree: six of the seven source files moved, `SKILL.md` alone by
+229/-44, and a new `references/starter-principles.md` (25 seed principles)
was classified entry by entry. Advanced from `v2.0.0` (`281f1346`) on
2026-08-31 the same way. The tag is pinned rather than the default branch: on
2026-09-05 the branch was one commit ahead (`2967fa5f`, `CONTRIBUTING.md`
only) and all eight source files were byte-identical at both, so the tag is the
same bytes with a name that does not move.

The upstream work is licensed under the
[Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/).

This adaptation changes the upstream design by making activation and writes
explicitly opt-in, storing observations as an append-only locked JSONL event
ledger outside any repository, and prohibiting automatic edits, deployment,
commits, deletion, or scheduled application.

One divergence listed here until 2026-08-31 has narrowed. Against `v2.0.0` this
skill contrasted with "a mutable numbered Markdown log"; `v3.0.0` replaced that
with one file per observation and deleted the numbering ritual, on the same
reasoning this adaptation used — a write that touches no other entry's bytes
cannot truncate or renumber one. The storage differs still (a locked JSONL
event stream against per-file Markdown with frontmatter), but the hazard both
designs avoid is now the same hazard, so the sentence no longer claims the
upstream carries it.

The rest of the `agent-harness` repository remains under its existing licence;
this notice applies to the adapted task-observer material.
