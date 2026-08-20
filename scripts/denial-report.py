#!/usr/bin/env python3
"""Read the denial log. Reports; never fails.

Why this exists. `denial_log` was built on 2026-08-08 to answer one question -
how often do our gates block, and whom - and it deliberately collected the data
before anything consumed it, because deciding whether any threshold is warranted
needs the data first. That was the right order and then nothing consumed it for
twelve days, which was long enough for the log to reach 35,856 rows of which 3
were real without anyone noticing. An instrument nobody reads cannot tell you it
has broken; that is the whole argument for this file existing.

What it answers. Per gate and per reason, how often a boundary fired, and how
that moves across days. An escape hatch reached for often is a statement about
the gate's condition, not about the person who reached for it, so these counts
are the input to "is this gate written wrong" rather than to anything about a
user.

What it deliberately does not do. Decide. No threshold, no non-zero exit, no
escalation. The threshold that was proposed once - three consecutive denials -
was checked on 2026-08-10 and turned out to measure ordinary work: the commit
gate denies repeatedly while a red suite gets fixed, which is the mechanism
succeeding. The longest-run column is printed for that reason and left there.

Provenance. Rows recorded before 2026-08-20 include the suite's own fixture
denials: the gates resolve their log path from HOME, the tests run those gates
for real, and most fixtures - but not all of them - override HOME. They are
counted apart rather than filtered out, because deciding which rows are fake
from their contents is a judgement this script would get wrong.

Usage:
    scripts/denial-report.py [--days N] [--json]
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The log path lives in one place. Importing it beats restating "~/.claude/
# telemetry/denials.jsonl" here, where it would drift the first time it moves.
_spec = importlib.util.spec_from_file_location(
    "denial_log", ROOT / "main/claude/hooks/denial_log.py")
_denial_log = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_denial_log)

# The day the suite stopped writing its fixture denials into the machine's log
# (main/claude/tests/support.py sets AGENT_DENIAL_LOG). Rows dated before this
# are a mixture and are reported as one.
ISOLATED_FROM = "2026-08-20"


def load(path: Path) -> tuple[list[dict], int]:
    rows, unparseable = [], 0
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            unparseable += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            unparseable += 1
    return rows, unparseable


def longest_run(rows: list[dict]) -> dict[str, tuple[int, str]]:
    """Per gate, the most consecutive rows it wrote, and when that run ended.

    Consecutive in file order, which is arrival order - the same order a person
    would have felt them.
    """
    best: dict[str, tuple[int, str]] = {}
    run_gate, run_len = None, 0
    for row in rows:
        gate = row.get("gate", "?")
        run_len = run_len + 1 if gate == run_gate else 1
        run_gate = gate
        if run_len >= best.get(gate, (0, ""))[0]:
            best[gate] = (run_len, row.get("ts", "")[:19])
    return best


def summarise(rows: list[dict], days: int) -> dict:
    by_gate = collections.Counter(row.get("gate", "?") for row in rows)
    by_reason = collections.Counter(
        (row.get("gate", "?"), row.get("reason", "?")) for row in rows)
    by_day = collections.Counter(row.get("ts", "")[:10] for row in rows)
    recent = sorted(by_day)[-days:] if days else sorted(by_day)
    return {
        "rows": len(rows),
        "first": rows[0].get("ts", "") if rows else "",
        "last": rows[-1].get("ts", "") if rows else "",
        "with_session": sum(1 for row in rows if row.get("session_id")),
        "before_isolation": sum(
            1 for row in rows if row.get("ts", "")[:10] < ISOLATED_FROM),
        "by_gate": dict(by_gate.most_common()),
        "by_reason": {f"{g} / {r}": n for (g, r), n in by_reason.most_common()},
        "by_day": {day: by_day[day] for day in recent},
        "longest_run": {g: {"rows": n, "ended": ts}
                        for g, (n, ts) in sorted(longest_run(rows).items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=14,
                        help="how many recent days to break out (0 = all)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(_denial_log.log_path())
    rows, unparseable = load(path)
    report = summarise(rows, args.days)
    report["log"] = str(path)
    report["bytes"] = path.stat().st_size if path.exists() else 0
    report["unparseable"] = unparseable

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"denial log: {report['log']}")
    if not rows:
        print("no denials recorded")
        return 0
    print(f"{report['rows']} row(s), {report['bytes'] / 1024:.0f} KiB, "
          f"{report['first'][:10]} .. {report['last'][:10]}")
    if unparseable:
        print(f"  {unparseable} unparseable line(s), skipped")

    stale = report["before_isolation"]
    if stale:
        print(f"  {stale} row(s) predate {ISOLATED_FROM} and include the "
              f"suite's own fixture denials; counts below mix them in")
    print(f"  {report['with_session']} row(s) carry a session id")

    print("\nby gate and reason")
    for label, count in report["by_reason"].items():
        print(f"  {count:8d}  {label}")

    print(f"\nby day (last {args.days or 'all'})")
    for day, count in report["by_day"].items():
        print(f"  {count:8d}  {day}")

    print("\nlongest consecutive run per gate")
    for gate, run in report["longest_run"].items():
        print(f"  {run['rows']:8d}  {gate}  (ended {run['ended']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
