"""Shared fixtures and helpers for the contract test suite."""
from __future__ import annotations

import ast

import json
import os
import re
import subprocess
import sys
import tempfile

# Fail with the actual cause before `import tomllib` fails with a misleading
# one. Below 3.11 every module in this suite dies on that import, and unittest
# reports it as an error in each test file — a wall of red that reads like the
# harness is broken. It happened for real: /usr/bin/python3 is 3.9 on macOS, so
# any agent or hook that inherits the system PATH lands here. commit-test-gate
# resolves an interpreter for exactly this reason; the suite should say the
# same thing when it is run by hand.
if sys.version_info < (3, 11):
    raise SystemExit(
        f"agent-harness tests need Python >= 3.11 for stdlib tomllib; this is "
        f"{sys.version.split()[0]} at {sys.executable}. Run the suite with a "
        f"newer interpreter (and put it on PATH — subprocess-spawned scripts "
        f"resolve `python3` themselves)."
    )

import tomllib  # noqa: E402  (guarded above; the guard must run first)
import unittest  # noqa: E402
from collections import namedtuple  # noqa: E402  (after the version guard)
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Detach the suite from whatever repository its caller was working in, once,
# before any fixture runs. Many tests here create a scratch repository and make
# real commits in it; with `GIT_DIR` or `GIT_INDEX_FILE` inherited, those writes
# land in the *caller's* repository instead. Git exports exactly these to every
# hook it runs, so the git-side `pre-commit` gate - which runs this suite from
# inside a commit - pointed every fixture at the developer's own HEAD and index
# and moved HEAD onto fixture commits (reproduced 2026-08-04).
#
# The gate scrubs its own subprocess environment too. This is the half that
# holds when the suite is run by hand from a shell that happens to have them
# set, and it is here rather than in each fixture because "every `git` this
# suite runs must be repository-neutral" is a property of the suite, not
# something 40 call sites should each remember.
GIT_HOOK_ENV = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX", "GIT_COMMON_DIR",
    "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES", "GIT_QUARANTINE_PATH",
    "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_AUTHOR_DATE",
    "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_COMMITTER_DATE",
    "GIT_EDITOR", "GIT_EXEC_PATH",
)
for _name in GIT_HOOK_ENV:
    os.environ.pop(_name, None)

# Send every denial this suite provokes somewhere that is not the developer's
# machine. The same argument as the scrub above, one layer over: these tests run
# the fail-closed gates for real, so they produce real denial rows, and
# `denial_log` resolves its path from HOME. Most fixtures already override HOME;
# the ones that cannot - a spelling test needs `~` to mean the real home - wrote
# into the machine-local log instead, and by 2026-08-20 it held 35,856 rows of
# which 3 were real. Setting it here rather than in each fixture, because "no
# test writes to the machine's telemetry" is a property of the suite.
os.environ["AGENT_DENIAL_LOG"] = os.path.join(
    tempfile.gettempdir(), "agent-harness-suite-denials.jsonl")


# Repo root: deployable harness sources live under main/; docs and evals stay
# at the project root.
ROOT = Path(__file__).resolve().parents[3]

ROLES = (
    "explore",
    "plan-verifier",
    "security-reviewer",
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
)
# Role spelling is lowercase on both providers since the 2026-07-23 rename.
CODEX_ROLES = ROLES
READ_ONLY_ROLES = (
    "explore",
    "plan-verifier",
    "verifier",
    "security-reviewer",
)
WRITER_ROLES = (
    "mech-executor",
    "executor",
    "security-executor",
)
BASH_ROLES = WRITER_ROLES
# Roles that must not be able to mutate the repository, whatever tools they hold.
# Mirrors the Codex twins' enforced sandbox_mode = "read-only".
NO_WRITE_ROLES = READ_ONLY_ROLES
# Role bodies are budgeted in words on both providers. `executor` is the
# largest at 378 (2026-07-26); raise this deliberately with a reason, the way
# the contract budgets are raised, rather than by lengthening lines.
ROLE_BODY_BUDGET = 400
# Density companions, one set for all fourteen bodies rather than one per role,
# because a role's rule count is a property of its job and not something a
# single ceiling should equalise. Widest measurements on 2026-08-04: `executor`
# at 21 rules, `mech-executor` at 123.4 bytes/rule and 0.291 filler,
# `plan-verifier` (codex) at 0.196 filler. See the metric definitions below.
ROLE_RULE_BUDGET = 24
ROLE_BYTES_PER_RULE = 135
ROLE_FILLER_RANGE = (0.17, 0.32)
# Every role pins model and effort from the active deployment preset (user-directed
# 2026-07-22); no role follows the main-session effort.
PINNED_EFFORT_ROLES = ROLES
FOLLOW_EFFORT_ROLES = ()

# Interface tokens: single upgrade point — bump here and in the skill bodies together.
CODEX_BRIDGE = "codex:codex-rescue"
DISPATCH_OPTIONS = ("Dispatch GPT + Claude", "Dispatch GPT", "Dispatch Claude")


def read(path: str) -> str:
    """Accepts the deployed (HOME-relative) path and resolves it to the source.

    Claude Code and Codex discover config from `.claude/` and `.codex/` below
    the working directory, so a source tree named that way competes with the
    deployed copy it exists to produce. Those two drop the dot in the repo and
    regain it from the manifest's target column at deploy time.

    `.agents/` keeps its dot. Nothing discovers it — it is this project's own
    convention rather than a standard — and both bundles reach the shared skills
    through relative symlinks (`../../.agents/skills/<name>`) that rsync copies
    verbatim. Those links must therefore resolve identically in the repo and in
    `$HOME`; renaming the shared root here would deploy 13 broken links.
    """
    return (ROOT / source_path(path)).read_text(encoding="utf-8")


def source_path(path: str) -> Path:
    """The repo-relative source behind a deployed (HOME-relative) spelling."""
    source = Path(path)
    if source.parts and source.parts[0] in {".claude", ".codex"}:
        return Path("main") / source.parts[0].lstrip(".") / Path(*source.parts[1:])
    if source.parts and source.parts[0] == ".agents":
        return Path("main") / source
    return source


def is_deployed(path: str) -> bool:
    """Whether the manifest ships `path`, directly or under a directory entry.

    This is the test for "does a session ever pay for this file". The manifest
    is the repo's only source->HOME mapping, so it is also the only answer that
    cannot drift from what actually deploys. A `.claude/` spelling is not
    sufficient on its own: `main/claude/plans/` lives in the bundle but ships
    nowhere.
    """
    posix = source_path(path).as_posix()
    return any(
        posix == source or posix.startswith(source.rstrip("/") + "/")
        for source, _ in deployment_manifest())


def deployment_manifest() -> list[tuple[str, str]]:
    return [(source, target) for source, target, _ in deployment_manifest_entries()]


def deployment_manifest_entries() -> list[tuple[str, str, str]]:
    entries = []
    for raw in read("scripts/deployment-manifest.tsv").splitlines():
        if not raw or raw.startswith("#"):
            continue
        fields = raw.split("\t")
        source, target = fields[:2]
        mode = fields[2] if len(fields) == 3 else ""
        entries.append((source, target, mode))
    return entries


def read_repo(path: str) -> str:
    """Literal repo-relative read. `read()` resolves deployed (HOME-relative)
    spellings, which silently rewrites a real repo path like
    `main/.agents/...` - fine for manifest work, wrong for a file listing."""
    return (ROOT / path).read_text(encoding="utf-8")


def exec_weekly_integrity_prelude(namespace: dict) -> None:
    """Define the hook's helpers without running its checks.

    Everything before the module's single top-level `try` is definitions; that
    block is the run. Slicing on a literal line of the file coupled a test to
    incidental wording once already, so the boundary is taken structurally.
    """
    source = read_repo("main/claude/hooks/weekly-integrity.py")
    body = ast.parse(source).body
    run_block = next(i for i, node in enumerate(body) if isinstance(node, ast.Try))
    exec(compile(ast.Module(body=body[:run_block], type_ignores=[]),
                 "<weekly-integrity prelude>", "exec"), namespace)


def assert_names(case, needle: str, document: str, message: str,
                 present: bool = True) -> None:
    """`assertIn` over a whole document, without printing the document.

    unittest renders both operands into the failure message, so asserting a
    phrase against a file puts the file in the output - 21 KB of architecture
    prose to say one phrase was missing. The suite is read by whoever or
    whatever is running it, and a failure nobody can see past is a failure that
    gets skimmed.

    Use it where the container is a document. Where it is a small fixture,
    a toml, or a role file, the standard assertion's output is short enough to
    be the evidence, and seeing it beats a message about it.
    """
    if (needle in document) is present:
        return
    verb = "does not contain" if present else "unexpectedly contains"
    case.fail(f"{message} [{len(document)} chars, {verb} {needle!r}]")


def carrier_pin() -> str:
    """The runtime `leaf-redispatch` records as having carried `agent_type`.

    Read from the hook so no test restates it: a pin that two files disagree
    about is worse than no pin, and the gate is the file an operator advances.
    """
    match = re.search(
        r"^CARRIER_VALIDATED_ON\s*=\s*\((\d+),\s*(\d+),\s*(\d+)\)",
        read_repo("main/claude/hooks/leaf-redispatch.py"), re.MULTILINE)
    if match is None:
        raise AssertionError("leaf-redispatch must pin its validated runtime")
    return ".".join(match.groups())


def deployed_skill_files() -> set[str]:
    """Every skill this repo ships, in the deployed spelling `read()` accepts.

    Enumerated from the repo's own skill roots rather than from `$HOME`:
    `~/.claude/skills` is a shared namespace, so listing the deployed directory
    would charge this repo for a third-party install. Symlinked shared skills
    appear once per provider because both are separately deployed surfaces.
    """
    found = set()
    for provider in ("claude", "codex"):
        root = ROOT / "main" / provider / "skills"
        for entry in sorted(root.iterdir()):
            if (entry / "SKILL.md").is_file():
                found.add(f".{provider}/skills/{entry.name}/SKILL.md")
    return found


def tracked_markdown() -> list[str]:
    """Every markdown file in the repo, repo-relative.

    Invariants about what the prose may claim are worth only as much as their
    file list: a hard-coded pair of filenames stops covering the docs the day
    someone documents the same mechanism in a third place.
    """
    listed = git("ls-files", "*.md").stdout.split()
    return [path for path in listed if not path.startswith("evals/")]


def covers(pattern: str, path: str) -> bool:
    """Glob match where `*` stops at a separator and `**` spans directories.

    `fnmatch` was used for the document inventory until 2026-08-19 and its `*`
    crosses `/`, so `docs/*.md` matched `docs/research/anything.md` and
    `main/claude/*.md` matched any depth under it. Every pattern was therefore
    recursive, which is how 77k words of lab journal spent three weeks inside
    the current-guidance envelope without anyone choosing that.
    """
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:[^/]+/)*"); i += 3
        elif pattern.startswith("**", i):
            out.append(".*"); i += 2
        elif pattern[i] == "*":
            out.append("[^/]*"); i += 1
        elif pattern[i] == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(pattern[i])); i += 1
    return re.fullmatch("".join(out), path) is not None


def document_inventory() -> dict:
    return json.loads(
        (ROOT / "docs/document-inventory.json").read_text(encoding="utf-8"))


def guidance_markdown() -> list[str]:
    """Tracked markdown that claims to be true right now.

    The complement is the evidence tier: journals that keep their refuted
    paragraphs and their original numbers on purpose. An invariant about what
    the prose may claim has to skip those, or it forces a lab notebook to be
    rewritten every time the mechanism it once described moves on.

    Precedence follows `pattern_precedence` in the inventory: an exact path
    beats a glob, which is what keeps `docs/research/README.md` in the guidance
    tier while its siblings sit outside it.
    """
    inventory = document_inventory()
    guidance = inventory["reviewed_current_guidance"]
    evidence = inventory["evidence_not_current_guidance"]
    excluded = inventory["excluded_from_semantic_currentness"]
    selected = []
    for path in tracked_markdown():
        if path in guidance:
            selected.append(path)
            continue
        if any(covers(rule, path) for rule in excluded):
            continue
        if any(covers(rule, path) for rule in evidence):
            continue
        if any(covers(rule, path) for rule in guidance):
            selected.append(path)
    return selected


def frontmatter(path: str) -> str:
    return read(path).split("---", 2)[1]


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
    )


def git_in(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """`git` against an arbitrary repository, for fixtures that build one."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )


def load_module(name: str, path: Path):
    """Import a harness script by path so its functions can be driven directly.

    Some boundaries can only be asserted by calling the real function - a test
    that greps the source for the fix cannot tell a working guard from one with
    the bug added back underneath it.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - path typo
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def word_count(text: str) -> int:
    """Budget unit: each CJK character counts as one word; other runs of
    non-space text count as one. Plain split() would let Chinese prose dodge
    the resident-attention budget entirely."""
    return len(re.findall(r"[\u4e00-\u9fff]|[^\s\u4e00-\u9fff]+", text))


# Companion ceiling to word_count: one unbroken run costs one word however long
# it is, so the word budget alone is evadable by a single giant token. The
# longest legitimate run across the budgeted files is a 106-character markdown
# link, so this leaves room for a long link without leaving room for a payload.
MAX_UNBROKEN_RUN = 200

# The run cap bounds one token; this bounds the whole file. Words approximate
# attention, not length, and the two ceilings compose badly: 520 words of
# 200-character runs passes both and is 104 KB, against ~2.8 KB for the real
# resident contract (2026-08-02 review). The widest budgeted file today sits at
# 8.6 bytes/word, so this is set to catch an order-of-magnitude deviation and
# nothing else - it must never become a second, tighter word budget.
MAX_BYTES_PER_WORD = 16

# Order-of-magnitude guard for the repo-only `docs/` tree, which carries no word
# budget (see test_deployed_prose_stays_distilled for why). Set at roughly 3x
# the largest document the tree has ever held, so that ordinary growth and an
# ordinary rewrite both pass and only a file that has stopped being one document
# fails. It is not a budget and must not be tuned toward one.
DOC_SPRAWL_CEILING = 20000

# The same failure one directory over, on the tree that had no guard at all.
# `test_mechanisms.py` reached 175 tests across 15 classes on 2026-08-20 - 45%
# of the whole suite in a file named "mechanisms" - while `docs/` had been
# guarded against exactly this since 2026-08-08.
#
# A share rather than a line count, deliberately. A line ceiling has to be
# raised as the suite grows and so becomes a second, tighter budget, which is
# what DOC_SPRAWL_CEILING's own comment warns against. A share is scale-free:
# adding tests anywhere raises the denominator, so ordinary growth never trips
# it and only concentration does. The remedy is to split the file at a subject
# seam, never to raise the constant.
TEST_SHARE_CEILING = 0.33


# Density companions to the word ceilings. A word cap bounds how large a
# document is; it says nothing about whether the words bought rules or padding,
# and at zero headroom it starts buying the wrong sentence rather than a shorter
# one - `.codex/AGENTS.md` sat at exactly 540/540 and a clause lost its
# grammatical subject to fit, inverting the guarantee it existed to make
# (c143b72, 2026-08-03).
#
# Three metrics, because each closes the others' cheat. Padding a rule shows up
# in bytes per rule; splitting one rule across several bullets to lower that
# average shows up in the rule count; deleting connective tissue until the prose
# stops parsing shows up in the filler ratio, which has a floor as well as a cap
# for that reason.
#
# They are added to the word ceilings, not swapped in for them. For density to
# bind first, the codex word cap would have to rise by roughly a quarter, and no
# evidence asks for a resident layer that much larger (2026-08-04).
def prose_only(text: str) -> str:
    """Contract prose with YAML frontmatter and fenced code removed.

    Neither behaves like a rule. Frontmatter is metadata the census budgets
    separately, and a fenced command block is one unit however many lines it
    spans - counting its lines as prose would make a file look denser the more
    commands it quotes.
    """
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    return re.sub(
        r"^```[^\n]*\n.*?^```[^\n]*\n", "", body, flags=re.DOTALL | re.MULTILINE)


_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[a-z]?[.)])\s+")
_SENTENCE_END = re.compile(r"(?<=[.!?。！？])\s+")


def rule_units(text: str) -> list[str]:
    """The countable obligations in a document body.

    A markdown list item is one rule, continuation lines included. Outside
    lists, one sentence of an ordinary paragraph is one rule. Headings count for
    nothing - they are navigation, and charging for them would price a
    well-signposted contract above an undifferentiated wall.
    """
    units: list[str] = []
    for block in re.split(r"\n\s*\n", prose_only(text)):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if any(_LIST_ITEM.match(line) for line in lines):
            item: list[str] = []
            for line in lines:
                if _LIST_ITEM.match(line):
                    if item:
                        units.append(" ".join(item))
                    item = [line.strip()]
                elif item:
                    item.append(line.strip())
            if item:
                units.append(" ".join(item))
            continue
        prose = " ".join(
            line.strip() for line in lines if not line.lstrip().startswith("#"))
        units.extend(part for part in _SENTENCE_END.split(prose) if part.strip())
    return units


def bytes_per_rule(text: str) -> float:
    """What one obligation costs to deliver, headings and all.

    The numerator is the whole prose body rather than the matched units, so
    scaffolding that carries no rule is charged to the rules it introduces.
    """
    units = rule_units(text)
    return len(prose_only(text).encode("utf-8")) / len(units) if units else 0.0


# Words that carry no obligation on their own: articles, copulas, demonstratives
# and the commonest prepositions and conjunctions. Modals and quantifiers
# (`must`, `may`, `never`, `only`, `every`) are deliberately absent - those are
# the operative words of a rule, and pricing them as filler would aim every edit
# at deleting exactly what the contract exists to say.
FILLER_WORDS = frozenset("""
a an the this that these those there here it its
and or but so then as of to in on at by for from with
is are was were be been being do does did have has had
""".split())


def filler_ratio(text: str) -> float:
    """Share of English words that are pure connective tissue.

    Latin-script words only: the CJK side of a bilingual document has no
    comparable closed class, and mixing the two would turn the ratio into a
    measurement of how much Chinese a file happens to contain.
    """
    words = re.findall(r"[a-z][a-z']*", prose_only(text).lower())
    return sum(w in FILLER_WORDS for w in words) / len(words) if words else 0.0


# One damage matrix for every JSONL reader in the harness. Six scripts parse
# the telemetry files - `experience-log`, `experience-stage`, the pending hook,
# `weekly-integrity`, `experience-report` and `experience-revise` - across two
# deployment trees, so they cannot share a decoder without coupling
# `~/.claude/hooks` to `~/.agents/skills`: sync one tree and not the other and
# the hook stops running altogether, which is worse than the divergence. They
# share this matrix instead, the same way the two `ledger_dispatch_ids`
# implementations are kept in step by a parity test.
#
# The count is load-bearing, not decoration: this comment said "four" while the
# last two only ever read the ledger, so they were never driven through the
# matrix and six of the seven classes aborted them (2026-08-02 review). A new
# reader that is not listed here is a reader nothing exercises.
#
# The second and third groups are the ones that got away twice. A corrupt byte
# raises before json.loads; valid-but-not-an-object raises after it, on the
# first `.get()`, as an AttributeError that neither `except json.JSONDecodeError`
# nor `except (OSError, ValueError)` catches (2026-07-31, both passes).
JSONL_DAMAGE = (
    ("corrupt_byte", b"\xff\xfe truncated\n"),
    ("truncated_multibyte", "{\"n\":\"半".encode("utf-8")[:-1] + b"\n"),
    ("malformed_json", b'{"ts":"2026-07-31T00:00:00+00:00","event":"Sub\n'),
    ("json_array", b"[]\n"),
    ("json_string", b'"junk"\n'),
    ("json_number", b"42\n"),
    ("json_null", b"null\n"),
)

# The layer above JSONL_DAMAGE: the row is a well-formed object and its
# *fields* are the wrong type. Every one of these is valid JSON that gets past
# an `isinstance(record, dict)` guard and then raises where nothing catches it -
# AttributeError inside `parse_ts`, TypeError from an unhashable cohort key, or
# TypeError comparing a naive timestamp with an aware one. The 2026-08-02 pass
# hardened the row shape and stopped there, so five of these still aborted both
# ledger readers (2026-08-03 review).
#
# `ts_naive` is the one to keep in mind when trimming this list: it is not
# damage at all, just a hand-written record without a zone.
JSONL_FIELD_DAMAGE = (
    ("ts_is_list", {"ts": []}),
    ("ts_is_number", {"ts": 42}),
    ("ts_is_null", {"ts": None}),
    ("ts_naive", {"ts": "2026-07-31T00:00:00"}),
    ("role_is_list", {"role": ["executor"]}),
    ("task_class_is_list", {"task_class": []}),
    ("provider_is_dict", {"provider": {}}),
    ("request_source_is_list", {"request_source": []}),
    ("profile_is_dict", {"profile": {}}),
    ("outcome_is_list", {"outcome": []}),
    ("route_source_is_list", {"route_source": []}),
)
