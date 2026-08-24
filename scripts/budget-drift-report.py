#!/usr/bin/env python3
"""Have the word ceilings been ratcheting, and where.

The per-document budgets in `test_contracts.py` are a ratchet, and the file says
so: growth has to displace something or be argued for in the commit message.
Nothing checked whether that held. Every ceiling today sits within a few percent
of its measured size, which is what a working ratchet looks like and also what a
rubber stamp looks like - the two are indistinguishable from one snapshot, and
only the history separates them.

So this reads the history. For each budget still in force: what it was first set
to, what it is now, how many times it was raised, and when it last moved.

What it is not. Not a gate, and deliberately without a threshold: the honest
reading of "this file's ceiling grew 60% in a month" depends on what the file
took on, which is a judgment the commit messages carry and a script cannot. It
also cannot tell a raise that displaced something from one that did not, because
displacement happens inside the file and the ceiling only sees the total.

The aggregate is printed last and on purpose. Growth here concentrates: a summary
that says "+6% overall" describes a tree where most ceilings never moved at all
and two files carry nearly all of it, which is the opposite of what a single
percentage suggests.
"""
from __future__ import annotations

import argparse
import ast
import collections
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "main/claude/tests/test_contracts.py"
# The assignment this report is about. Named once so a rename fails loudly here
# rather than silently reporting an empty history.
BINDING = "budgets"


def word_count(text: str) -> int:
    """Same unit as the deployed budgets: one per CJK character, one per other
    non-space run. Kept identical to `support.word_count` and to
    `resident-pool-report.py`, and a test holds the three together."""
    return len(re.findall(r"[一-鿿]|[^\s一-鿿]+", text))


def source_of(deployed: str) -> Path:
    """Where a deployed spelling lives in the checkout.

    `.claude/` and `.codex/` drop their dot under `main/`; `.agents/` keeps it.
    Same rule as the manifest, restated because a report has no business
    importing the test harness.
    """
    head, _, rest = deployed.partition("/")
    stem = {".claude": "main/claude", ".codex": "main/codex",
            ".agents": "main/.agents"}.get(head)
    return ROOT / (f"{stem}/{rest}" if stem else deployed)


def git(*args: str) -> str:
    done = subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else ""


def budgets_in(source: str) -> tuple[dict[str, int], list[str]] | None:
    """The `budgets` mapping, read as syntax rather than matched as text.

    A regex over a dict literal is the kind of parser that returns nothing when
    the formatting moves and reports it as "no history", which reads exactly
    like a ratchet that never moved. `ast` either finds the binding or does not.

    Two entries take their ceiling from a constant in `support.py` rather than a
    literal. Evaluating the dict as a whole fails on them, and dropping the
    whole binding for two entries - or silently keeping 17 of 19 and calling it
    the budget list - are both worse than reading pair by pair and naming what
    could not be read. The second half of the return value is those names.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if BINDING not in names or not isinstance(node.value, ast.Dict):
            continue
        literals: dict[str, int] = {}
        elsewhere: list[str] = []
        for key, value in zip(node.value.keys, node.value.values):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue
            try:
                ceiling = ast.literal_eval(value)
            except ValueError:
                elsewhere.append(key.value)
                continue
            if isinstance(ceiling, int):
                literals[key.value] = ceiling
            else:
                elsewhere.append(key.value)
        if literals or elsewhere:
            return literals, elsewhere
    return None


def history() -> list[tuple[str, str, dict[str, int]]]:
    """Every revision of the binding, oldest first."""
    log = git("log", "--format=%H %ad", "--date=short", "--", SOURCE)
    out = []
    for line in reversed(log.splitlines()):
        commit, _, day = line.partition(" ")
        read = budgets_in(git("show", f"{commit}:{SOURCE}"))
        if read is not None:
            out.append((commit, day.strip(), read[0]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args()

    revisions = history()
    read = budgets_in((ROOT / SOURCE).read_text(encoding="utf-8"))
    live, elsewhere = read if read else (None, [])
    if live is None:
        print(f"cannot read `{BINDING}` in {SOURCE}; this report is blind until "
              "that is fixed, and reporting nothing would look like no drift",
              file=sys.stderr)
        return 1
    if not revisions:
        print(f"no history for `{BINDING}` in {SOURCE}", file=sys.stderr)
        return 1

    first: dict[str, tuple[str, int]] = {}
    raises: collections.Counter[str] = collections.Counter()
    last_raise: dict[str, str] = {}
    previous: dict[str, int] = {}
    for _, day, mapping in revisions:
        for path, ceiling in mapping.items():
            if path not in first:
                first[path] = (day, ceiling)
            elif path in previous and ceiling != previous[path]:
                raises[path] += 1
                last_raise[path] = day
        previous = mapping

    rows = []
    for path, ceiling in sorted(live.items()):
        when, started = first.get(path, ("?", ceiling))
        source = source_of(path)
        used = word_count(source.read_text(encoding="utf-8")) if source.exists() else None
        rows.append({
            "path": path,
            "added": when,
            "first": started,
            "now": ceiling,
            "raises": raises[path],
            "growth_pct": (ceiling - started) / started * 100 if started else 0.0,
            "last_raise": last_raise.get(path),
            "used": used,
            "headroom_pct": None if used is None else (ceiling - used) / ceiling * 100,
        })

    if args.json:
        import json
        print(json.dumps({"source": SOURCE, "budgets": rows}, indent=2))
        return 0

    moved = [r for r in rows if r["raises"]]
    still = [r for r in rows if not r["raises"]]
    print(f"word ceilings in {SOURCE}: {len(rows)} with a literal ceiling"
          + (f" plus {len(elsewhere)} defined elsewhere" if elsewhere else "")
          + f", {len(revisions)} revisions of the binding")
    print()
    print(f"raised at least once ({len(moved)}):")
    for row in sorted(moved, key=lambda r: -r["growth_pct"]):
        print(f"  {row['raises']}x  {row['first']:>5} -> {row['now']:<5} "
              f"{row['growth_pct']:+6.1f}%  since {row['added']}, "
              f"last {row['last_raise']}  {row['path']}")
    print()
    print(f"never raised since added ({len(still)}):")
    for row in sorted(still, key=lambda r: r["path"]):
        print(f"        {row['now']:>5}          since {row['added']}  {row['path']}")

    started_total = sum(r["first"] for r in rows)
    now_total = sum(r["now"] for r in rows)
    share = (max((r["now"] - r["first"] for r in rows), default=0)
             / max(now_total - started_total, 1) * 100)
    print()
    print(f"total: {started_total} -> {now_total} "
          f"({(now_total - started_total) / started_total * 100:+.1f}%), "
          f"{sum(r['raises'] for r in rows)} raises across {len(moved)} file(s)")
    print(f"  concentration: the single largest raise accounts for {share:.0f}% "
          "of all growth, so read the rows and not this line")
    # The state this repo has already paid for once: on 2026-08-03 a contract
    # sitting at exactly 540/540 was compressed into a sentence that lost its
    # subject and inverted the guarantee the clause existed to make. Zero
    # headroom does not stop growth, it changes what growth costs.
    tight = sorted((r for r in rows if r["headroom_pct"] is not None
                    and r["headroom_pct"] < 2.0),
                   key=lambda r: r["headroom_pct"])
    if tight:
        print()
        print(f"under 2% headroom ({len(tight)}): the next edit here either "
              "displaces something or raises the ceiling")
        for row in tight:
            print(f"  {row['headroom_pct']:4.1f}%  {row['used']:>5}/{row['now']:<5} "
                  f" {row['path']}")

    if elsewhere:
        print()
        print(f"not tracked here ({len(elsewhere)}): the ceiling is a constant in "
              "support.py, so its history is that file's, not this binding's")
        for path in elsewhere:
            print(f"        {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
