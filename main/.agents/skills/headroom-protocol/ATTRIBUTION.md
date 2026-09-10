# Attribution — headroom-protocol

**Origin**: this repository. Written for this harness on 2026-07-15 as the
manual compression path around the Headroom proxy, and not distilled from any
other project's skill or prompt.

**What it depends on, which is not the same as where it came from.** The skill
drives the Headroom MCP tools (`headroom_compress`, `headroom_retrieve`,
`headroom_stats`) and names `headroom doctor`. Headroom is a dependency this
repo runs, listed as 相依 in `docs/research/README.md`'s currency table; its
tool names appear here because they are the interface, and nothing of its
documentation or prompts is reproduced. Version and lifecycle facts live in
`main/.agents/docs/headroom-runtime.md`, not here.

**Checked on 2026-09-10** (the plan's Q10 trace): the research tier names
Headroom in one role only, as the tool being wrapped; no ledger row, landing
note or attribution anywhere in the tree records a rule of this skill as
adopted from elsewhere. The Claude thin wrapper beside the shared body
(`main/claude/skills/headroom-protocol/SKILL.md`) is local text as well and
links this file.
