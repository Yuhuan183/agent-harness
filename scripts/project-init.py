#!/usr/bin/env python3
# Read: before installing the project layer into a repository, and when `--verify` reports a block has drifted
"""Render one repository's fact bundle and merge it as a fenced block.

The global harness under HOME carries authority - roles, dispatch,
verification, gates - and travels with the person. This script installs the
other half into a repository: facts about that repository, which travel with
it and which the client injects every turn through the project CLAUDE.md and
AGENTS.md it already reads. Nothing here says what to do next; that sentence
belongs to the global contract, and `test_project_layer.py` holds the
templates to it.

The facts live in exactly one place, `<repo>/.agent-harness/facts.toml`, and
both contract blocks are rendered from it. The first `--apply` on a repository
writes the skeleton and stops: an empty value is an unanswered question, and a
block with a hole in it would ship as prompt text. Filled facts render into a
fenced block (`<!-- agent-harness:start -->` ... `end`) that is merged into the
target file - created if absent, appended if the team already has one, replaced
in place if the markers are there - so nothing outside the block is touched.

Usage:
  scripts/project-init.py <repo>            dry-run: what would change, and the diff
  scripts/project-init.py <repo> --apply    write the skeleton, or render and merge
  scripts/project-init.py <repo> --verify   0 current, 1 drifted, 4 not installed

Exit codes: 0 ok, 1 block drifted or malformed, 3 facts missing or unfilled,
4 not installed (verify only), 5 refused - the repository is this checkout or
a target would land on a path the global manifest manages.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_MANIFEST = ROOT / "scripts/project-manifest.tsv"
GLOBAL_MANIFEST = ROOT / "scripts/deployment-manifest.tsv"
FACTS_EXAMPLE = ROOT / "main/project/facts.example.toml"
FACTS_RELATIVE = Path(".agent-harness/facts.toml")
START, END = "<!-- agent-harness:start -->", "<!-- agent-harness:end -->"
SLOT = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")
BLOCK = re.compile(re.escape(START) + r"\n.*?\n" + re.escape(END), re.S)

EXIT_OK, EXIT_DRIFT, EXIT_FACTS, EXIT_NOT_INSTALLED, EXIT_REFUSED = 0, 1, 3, 4, 5

#: Ceiling on a rendered block, in the suite's word units. The block is resident
#: in every session of the repository, so it pays like a contract. Set after the
#: first real fill (game-client-sdk, 2026-09-11: 238 words with three traps and
#: three lenses) with room for a couple more facts, not a couple more paragraphs.
#: `--apply` still writes past it and says so; `--verify` reports it as drift,
#: so a fat block is a red check rather than a silent tax.
RENDERED_BLOCK_CEILING = 260


def manifest_rows(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        fields = raw.split("\t")
        rows.append((fields[0], fields[1], fields[2] if len(fields) > 2 else ""))
    return rows


def word_count(text: str) -> int:
    """The suite's budget unit: one per CJK character, one per other run."""
    return len(re.findall(r"[一-鿿]|[^\s一-鿿]+", text))


def refusal(repo: Path, rows: list[tuple[str, str, str]]) -> str | None:
    """A target that resolves onto a HOME-managed path, or this checkout."""
    if repo.resolve() == ROOT.resolve():
        return ("this checkout is the source of the project layer, not a target; "
                "its rules are its own tests")
    if repo.resolve() == Path.home().resolve():
        return ("HOME is the global layer's target, never the project layer's; "
                "a root CLAUDE.md there would be read by every session on this machine")
    managed = {(Path.home() / target).resolve() for _, target in
               ((s, t) for s, t, *_ in manifest_rows(GLOBAL_MANIFEST))}
    for _, target, _ in rows:
        if (repo / target).resolve() in managed:
            return (f"{repo / target} is a path the global manifest deploys to; "
                    "the project layer never writes where the global layer does")
    # Two targets, one inode. Three of the five contract-bearing repositories in
    # the workspace this was built for keep `CLAUDE.md` as a symlink to
    # `AGENTS.md`, and measured 2026-09-11 the collision was silent: both writes
    # reported success, the exit code was 0, and one block survived - the second
    # one, because `merged` found the first between the same markers and
    # replaced it. A Claude session following the link then read the Codex
    # wording of every fact. Refused rather than resolved: which client's block
    # should win is a question for whoever made the two names one file.
    seen: dict[Path, str] = {}
    for _, target, _ in rows:
        resolved = (repo / target).resolve()
        if resolved in seen:
            return (f"{repo / target} and {repo / seen[resolved]} are the same "
                    "file (one is a link to the other); the second block would "
                    "replace the first between the same markers, leaving one "
                    "client's wording for both")
        seen[resolved] = target
    return None


def load_facts(path: Path, required: set[str]) -> tuple[dict | None, list[str]]:
    """The facts, or the list of problems that stop rendering."""
    try:
        facts = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        return None, [f"{path}: not valid TOML ({error})"]
    problems = []
    for key in sorted(required):
        value = facts.get(key)
        if isinstance(value, str):
            filled = bool(value.strip())
        elif isinstance(value, list):
            filled = bool(value) and all(isinstance(v, str) and v.strip() for v in value)
        else:
            filled = False
        if not filled:
            problems.append(f"{key}: unanswered")
        elif "{{" in (value if isinstance(value, str) else " ".join(value)):
            problems.append(f"{key}: carries a slot marker, which would ship as residue")
    for key in sorted(set(facts) - required):
        problems.append(f"{key}: not a fact the templates ask for")
    return (facts if not problems else None), problems


def render(template: str, facts: dict) -> str:
    def fill(match: re.Match) -> str:
        value = facts[match.group(1)]
        if isinstance(value, list):
            return "\n".join(f"  - {item}" for item in value)
        return value
    rendered = SLOT.sub(fill, template).strip()
    if "{{" in rendered:
        raise ValueError("a slot survived rendering")
    return f"{START}\n{rendered}\n{END}"


def merged(existing: str | None, block: str) -> str:
    if existing is None:
        return block + "\n"
    if existing.count(START) == 1 and existing.count(END) == 1:
        return BLOCK.sub(lambda _: block, existing, count=1)
    return existing.rstrip("\n") + "\n\n" + block + "\n"


def current_block(existing: str | None) -> str | None:
    if existing is None:
        return None
    found = BLOCK.findall(existing)
    return found[0] if len(found) == 1 and existing.count(START) == 1 else None


def diff(before: str, after: str, name: str) -> str:
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=f"{name} (current)", tofile=f"{name} (rendered)"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install or verify a repository's agent-harness fact block.")
    parser.add_argument("repo", type=Path, help="repository root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="write instead of planning")
    mode.add_argument("--verify", action="store_true",
                      help="compare installed blocks against the rendered ones")
    args = parser.parse_args()
    repo: Path = args.repo
    if not repo.is_dir():
        print(f"ERROR: {repo} is not a directory", file=sys.stderr)
        return 2

    rows = manifest_rows(PROJECT_MANIFEST)
    reason = refusal(repo, rows)
    if reason:
        print(f"REFUSED: {reason}", file=sys.stderr)
        return EXIT_REFUSED

    templates = {target: (ROOT / source).read_text(encoding="utf-8")
                 for source, target, _ in rows}
    required = {slot for text in templates.values() for slot in SLOT.findall(text)}

    facts_path = repo / FACTS_RELATIVE
    if not facts_path.is_file():
        if args.apply:
            facts_path.parent.mkdir(parents=True, exist_ok=True)
            facts_path.write_text(FACTS_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"wrote the facts skeleton: {facts_path}")
        else:
            print(f"[dry-run] would write the facts skeleton: {facts_path}")
        print("fill every fact, then run again; nothing renders until each "
              "question has an answer", file=sys.stderr)
        return EXIT_FACTS

    facts, problems = load_facts(facts_path, required)
    if problems:
        print(f"{facts_path}:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return EXIT_FACTS

    status = EXIT_OK
    for target, template in templates.items():
        path = repo / target
        block = render(template, facts)
        existing = path.read_text(encoding="utf-8") if path.is_file() else None
        installed = current_block(existing)
        words = word_count(block)
        label = f"{target} ({words} words in the block)"
        over = words > RENDERED_BLOCK_CEILING

        if args.verify:
            if installed is None:
                print(f"{target}: not installed")
                status = max(status, EXIT_NOT_INSTALLED)
            elif installed != block:
                print(f"{target}: block drifted from the rendered facts")
                print(diff(installed, block, target), end="")
                status = max(status, EXIT_DRIFT) if status != EXIT_NOT_INSTALLED else status
            elif over:
                print(f"{target}: current, but {words} words is past the "
                      f"{RENDERED_BLOCK_CEILING}-word ceiling; trim the facts, "
                      "every session here pays for them")
                status = max(status, EXIT_DRIFT) if status != EXIT_NOT_INSTALLED else status
            else:
                print(f"{target}: current")
            continue

        if over:
            print(f"WARNING: {label} is past the {RENDERED_BLOCK_CEILING}-word "
                  "ceiling; --verify will report it until the facts are trimmed",
                  file=sys.stderr)

        if existing is not None and (existing.count(START) != existing.count(END)
                                     or existing.count(START) > 1):
            print(f"ERROR: {path} has unbalanced or repeated markers; fix by hand",
                  file=sys.stderr)
            return EXIT_DRIFT
        after = merged(existing, block)
        if existing == after:
            print(f"{label}: already current")
            continue
        if args.apply:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(after, encoding="utf-8")
            print(f"wrote {label}")
        else:
            verb = "create" if existing is None else "update"
            print(f"[dry-run] {verb} {label}")
            print(diff(existing or "", after, target), end="")
    return status


if __name__ == "__main__":
    sys.exit(main())
