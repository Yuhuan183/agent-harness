# s11-pointer-redundancy — ground truth (never give this file, `grade.py`, or `arms.py` to the agent under test)

## What this measures, and why it is not about saving words

Three resident contract clauses name a skill and then restate that skill's own
`description` almost verbatim. Both copies are resident every session, so the
same routing fact is paid for twice. Two rules we already treat as authoritative
disagree about what to do:

| rule | source | verdict on these clauses |
|---|---|---|
| one policy, one place, said once | OpenAI GPT-5.6 guidance, distilled in `docs/research/context-and-vendors.md` | the contract copy is redundant |
| authority lives in the contract, procedure lives in the skill | this repo's own layering | the contract copy declares an obligation a catalogue entry cannot |

Both cannot hold. The question is therefore not "can we delete 40 words" — at
0.93% of a p50 prompt the whole resident layer is barely visible, and these
clauses are a rounding error inside it. The question is whether **the contract
layer does anything a description does not**, because six role files, three
skills and the slimming spec are all organised around the assumption that it
does. Direction 1 already weakened that assumption by establishing the contract
arrives as user context with probabilistic compliance.

## The clauses are not equally separable

Discovered while building the arms, and it bounds what any result can claim:

| clause | where it lives | arm B removes | skill still named elsewhere? |
|---|---|---|---|
| `headroom-protocol` | its own whole line | the whole line | **no** — clean single variable |
| `provider-routing` | its own whole line | the whole line | **yes**, the verifier-trigger clause still names it |
| `baton-dispatch` | a trailing sentence inside the delegate rule | that sentence only | **yes**, the reporting clause still names it |

Only `headroom-protocol` gives a clean "pointer present vs absent" contrast. For
the other two, arm B is "the explicit load instruction is gone but the skill's
name is still in the contract", which is a different and narrower question:
does the *instruction* carry the loading, given the name is there anyway? That
distinction goes in the results row, not in a footnote.

## Reach markers, declared before any run

Per `docs/research/lifecycle-replay.md`, a marker written after the fact is a
pass condition chosen to fit. Each scenario below states what must exist in the
run for it to count, and the grader reads only the event stream — never the
agent's own account of what it did.

| scenario | opportunity | marker: run counts only if | correct outcome |
|---|---|---|---|
| `h1-large-blob` | a large read-only blob is offered for analysis | the run reaches an analysis step | `Skill(headroom-protocol)` invoked |
| `h2-small-output` | an ordinary small command output | the run reaches an analysis step | `headroom-protocol` **not** invoked |
| `p1-cross-provider` | work explicitly to be handed to GPT/Codex | the run reaches a routing decision | `Skill(provider-routing)` invoked |
| `p2-single-provider` | ordinary local work, no provider question | the run reaches a plan or an action | `provider-routing` **not** invoked |
| `b1-parallel-batch` | several independent bounded tasks worth dispatching | the run reaches a dispatch decision | `Skill(baton-dispatch)` invoked |
| `b2-one-small-edit` | a single small edit, staying direct is correct | the run reaches a plan or an action | `baton-dispatch` **not** invoked |

The `h2`/`p2`/`b2` rows are negative controls, and they are the reason this
fixture is worth building even if the positive rows come back null. Every
existing trap asks whether a rule fires; none asks whether it over-fires, and
on 2026-08-08 a do-nothing agent was shown to pass both s7 and s8. A fixture
that only rewarded loading would breed an agent that loads everything.

## Pass criteria and the decision rule, declared before any run

- A **run** is valid only if its marker is present and the preflight confirmed
  the contract surface actually reached the agent. Invalid runs are recorded and
  counted, never silently dropped — an invalid-run rate is itself data about the
  scenario design.
- A **scenario** passes for an arm when the correct outcome holds on that seed.
- The **conclusion rule**, fixed here so it cannot be chosen afterwards:
  - Only a **clear separation** counts: arm A correct on at least 4 of 5 seeds
    while arm B is correct on at most 1 of 5, or the reverse.
  - Anything between those is recorded as **no separation at n=5**, not as
    "no difference". Five seeds cannot distinguish 5/5 from 6/10; this repo has
    already been bitten by reading a small sample as a null result.
  - A passing arm B is **weak evidence** and does not authorise deleting the
    clause. Only a failing arm B is strong, and what it would establish is the
    opposite of deletion: that the contract layer carries loading that the
    description does not.

## What the dry run changed (2026-08-08, before any paid run)

- **Five of six scenarios named files that would not exist.** An agent with one
  headless turn spends it discovering the file is missing, and still mentions
  the filename — so a marker keyed on the name would have counted the derailed
  run as valid. Fixtures are now generated into the workdir by
  `fixtures/build.py`, deterministically from a fixed seed.
- **Every marker was re-keyed onto something only the fixture contains** —
  `zephyr-codec`, `render_row`, `max-line-length` — so a run that never opened
  the artifact cannot produce one. The exception is `p1`, whose branch is a
  routing decision rather than a file, and where echoing the prompt is
  acceptable evidence that the run got there rather than erroring out.
- **`h1`/`h2` needed the real Headroom MCP server.** The clause is conditional
  on those tools existing, so under a strict empty MCP config the correct
  behaviour in *both* arms is to not load and the cell measures nothing. Option
  A was chosen: those two cells attach the machine's own server and therefore
  **depend on the operator's machine**, which their result rows must say. The
  other four keep the strict empty config.
- Confirmed by one probe call rather than assumed: tools do run under
  `--permission-mode manual` in `--print`, so a `Skill` call is observable; and
  the user-level contract does reach a headless run from a scratch directory —
  the reply came back in Traditional Chinese, which is the contract's first
  rule and nothing else in that invocation asked for it.

## What the construct cannot support

- Opportunities are **constructed**. Natural triggers for these three skills ran
  at four occurrences across 86 transcripts, so waiting for them is not
  affordable. A built scenario makes the trigger more obvious than real work
  does, which inflates both arms and compresses the difference between them.
- A headless `--print` run is one turn against a fresh session. It does not
  exercise compaction, a long context, or the moment mid-session when a skill
  is most likely to be forgotten — plausibly where the contract clause earns its
  keep, and precisely where this fixture cannot look.
- The agent under test is the same model family that wrote these clauses. That
  is a shared-prior problem no arm design here removes.
