You are starting a fresh session in a harness that has six skills installed.

`descriptions.md` in your working directory is the complete routing surface that
session carries: for each installed skill, its name and the description that sits
in context from the first turn. `utterances.md` lists eighteen things a user
might say as their opening message.

Outcome: for each utterance, decide which single installed skill (if any) should
be loaded to handle it, using only what the descriptions say.

Scope: read the two files and decide. Do not open, look for, or reason from any
other file — the skill bodies are not in scope and are not available; a
description is all a session has when it makes this choice. Change nothing;
create no files other than your report.

Rules:

- Exactly one skill per utterance, or `none`.
- `none` means no installed skill's description covers that ask. An ask can be
  outside every skill's subject, and an ask can be inside a skill's subject but
  ruled out by that skill's own 不觸發 / "Not for" clause. Both are `none`.
- Do not load a skill because the topic is adjacent. Load it when its
  description says it handles that ask.

Output: your report must contain one line per utterance, at column one, in
exactly this shape and nothing else on the line:

```text
SELECT: U01 -> readable-zh-tw
SELECT: U06 -> none
```

Eighteen such lines, `U01` through `U18`. Put any reasoning after them; the
lines are what is read.

Stops: if a description is ambiguous for an utterance, still commit to one
answer and note the ambiguity below the lines. Do not ask a clarifying
question — the point of the exercise is the decision the surface supports.
