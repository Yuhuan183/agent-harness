#!/usr/bin/env python3
"""What a session on this machine actually carries, and how much of it is budgeted.
Reports; never fails.

`scripts/prompt-surface-census.py` measures the skills this repo ships, and
`test_resident_skill_metadata_stays_within_budget` ratchets them. Both are
deterministic because both read the checkout - which is also their limit: every
skill installed from somewhere else is listed in exactly the same per-session
block and no mechanism here has ever seen it. On 2026-08-17 that was 8 managed
skills inside a pool of 49, so the ratchet everybody pays attention to reached
about a sixth of the load it appears to control (M5 finding, see
docs/plans/engineering-workflow-distillation.md).

That gap cannot be closed by a gate. The other 41 are not this repo's files, and
a commit hook that fails because the user installed a skill would be refusing
work it has no standing to refuse. So this is the instrument instead, on the
same argument that made `docs/` a report rather than a budget: measure it, print
it, and let the reader decide.

Two things it deliberately does not do. It does not fail, so nothing here can be
paid off by deleting a skill. And it does not feed the census - that stays
checkout-only, because a contract test whose result depends on machine state is
a test that passes or fails for reasons the commit cannot explain.

WHAT IT CANNOT SEE, so the total below is a floor and not the whole:
  - skills built into the CLI (artifact-design, dataviz, code-review ...), which
    live in the binary rather than on disk;
  - plugin skills, which are on disk but under version directories where the
    installed set and the *enabled* set differ - counting them would report
    skills no session lists.
Both are listed in the session block alongside the ones counted here.

Usage:
    scripts/resident-pool-report.py [--json] [--top N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POOL = Path.home() / ".claude" / "skills"
# The same directory `evals/replay/run.py:resident_skills()` writes into every
# run's meta, so a coverage figure from here and a pool recorded there describe
# one surface and can be compared.

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def word_count(text: str) -> int:
    """Same unit as the deployed budgets: one per CJK character, one per other
    non-space run. Kept identical so this report and the census are comparable."""
    return len(re.findall(r"[一-鿿]|[^\s一-鿿]+", text))


def resident_fields(skill_md: Path) -> str | None:
    """`name` and `description` only - the two fields a session is handed.

    The body is dispatch cost, paid once by whoever loads the skill, and the
    rest of the frontmatter is not quoted into the session block at all. An
    earlier hand measurement counted the whole frontmatter and reached 5324
    words where this unit reaches 4894; the ratio was unaffected because both
    halves were measured the same way, but only one of the two is what a turn
    actually pays.
    """
    match = FRONTMATTER.search(skill_md.read_text(encoding="utf-8"))
    if not match:
        return None
    fields: dict[str, str] = {}
    lines = match.group(1).splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        key, separator, value = line.partition(":")
        key = key.strip()
        scalar = value.strip()
        if separator and not line[:1].isspace() and key in {"name", "description"}:
            if scalar in {"|", "|-", "|+", ">", ">-", ">+"}:
                block: list[str] = []
                index += 1
                while index < len(lines):
                    continuation = lines[index]
                    if continuation and not continuation[:1].isspace():
                        break
                    block.append(continuation.strip())
                    index += 1
                fields[key] = ("\n" if scalar.startswith("|") else " ").join(
                    block).strip()
                continue
            fields[key] = scalar.strip("\"'")
        index += 1
    if "description" not in fields:
        return None
    return f"{fields.get('name', skill_md.parent.name)} {fields['description']}"


def managed_names() -> set[str]:
    """Deployed-or-not is the criterion, exactly as contract-slimming.md states.

    Read from the manifest rather than hardcoded, so a skill added to the
    shipping layer moves across this line on the same commit that ships it.
    """
    names = set()
    for line in (ROOT / "scripts/deployment-manifest.tsv").read_text(
            encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].startswith(".claude/skills/"):
            names.add(parts[1].rsplit("/", 1)[-1])
    return names


def project_skills() -> list[Path]:
    """Dev-only skills of this checkout: resident in every session opened here.

    They are outside the census by design (they do not ship) but inside the
    per-skill cap, for the reason contract-slimming.md gives - the one skill
    outside the ratchet was resident in the most frequently opened repo.
    """
    root = ROOT / ".claude" / "skills"
    if not root.is_dir():
        return []
    return sorted(p / "SKILL.md" for p in root.iterdir()
                  if (p / "SKILL.md").is_file())


def measure() -> dict:
    managed = managed_names()
    rows = []
    for skill_md in sorted(POOL.glob("*/SKILL.md")) + project_skills():
        text = resident_fields(skill_md)
        if text is None:
            continue                       # no description: nothing is resident
        name = skill_md.parent.name
        rows.append({
            "name": name,
            "origin": ("repo-managed" if name in managed
                       else "project" if ROOT in skill_md.parents
                       else "unmanaged"),
            "words": word_count(text),
            "bytes": len(text.encode("utf-8")),
        })
    return {
        "unit": "word_count over `name` + `description`, CJK-aware",
        "pool": POOL.as_posix(),
        "floor": True,                     # see the module docstring
        "skills": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable")
    parser.add_argument("--top", type=int, default=10,
                        help="widest unbudgeted descriptions to list (0 for all)")
    args = parser.parse_args()

    if not POOL.is_dir():
        print(f"no skill pool at {POOL}; nothing resident to measure here")
        return 0

    report = measure()
    rows = report["skills"]
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    if not rows:
        print(f"{report['pool']}: no skill carries a description")
        return 0

    def total(origin: str) -> tuple[int, int]:
        picked = [row for row in rows if row["origin"] == origin]
        return len(picked), sum(row["words"] for row in picked)

    everything = sum(row["words"] for row in rows)
    print(f"resident skill metadata, {report['unit']}")
    print(f"pool: {report['pool']} plus this checkout's dev-only skills\n")
    for origin, note in (
            ("repo-managed", "per-skill cap and a per-provider total"),
            ("project", "per-skill cap only"),
            ("unmanaged", "no mechanism"),
    ):
        count, words = total(origin)
        share = f"{100 * words / everything:5.1f}%" if everything else "    -"
        unit = "skill " if count == 1 else "skills"
        print(f"  {origin:<13} {count:>3} {unit} {words:>6}w  {share}   {note}")
    print(f"  {'total':<13} {len(rows):>3} skills {everything:>6}w"
          "           a floor: CLI-builtin and plugin skills are not counted")

    unmanaged = sorted((row for row in rows if row["origin"] == "unmanaged"),
                       key=lambda row: -row["words"])
    if unmanaged:
        shown = unmanaged if args.top == 0 else unmanaged[:args.top]
        print(f"\nwidest with no mechanism ({len(shown)} of {len(unmanaged)}):")
        width = max(len(row["name"]) for row in shown)
        for row in shown:
            print(f"  {row['name']:<{width}}  {row['words']:>4}w  {row['bytes']:>6}B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
