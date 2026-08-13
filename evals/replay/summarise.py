#!/usr/bin/env python3
"""Build the results table for a replay batch from the runs themselves.

The table in `README.md` is not typed by hand. Earlier in this line of work a
row was hand-transcribed from an agent's own report and the transcription was
the error; the rule that came out of it is that a number a reader will cite has
to be recomputed from artifacts by something that can be re-run. This is that
something.

Rates carry an exact (Clopper-Pearson) 95% interval, computed here rather than
imported, because the interesting part of a small clean batch is the lower
bound: 5 for 5 is entirely compatible with a true rate near one in two, and a
results table that prints `100%` without the interval invites the opposite
reading.

Invalid runs are shown in their own column and excluded from the rate's
denominator — `docs/research/lifecycle-replay.md` says an unreached run is
neither a pass nor a failure, but that its count is itself data.

    summarise.py [--runs evals/replay/runs] [--json]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import Counter
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent


def clopper_pearson(hits: int, total: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact binomial interval, by bisection on the tail sums."""
    if total == 0:
        return (0.0, 1.0)

    def at_least(p: float) -> float:
        return sum(comb(total, i) * p ** i * (1 - p) ** (total - i)
                   for i in range(hits, total + 1))

    def at_most(p: float) -> float:
        return sum(comb(total, i) * p ** i * (1 - p) ** (total - i)
                   for i in range(0, hits + 1))

    low, high = 0.0, 1.0
    if hits > 0:
        a, b = 0.0, 1.0
        for _ in range(120):
            mid = (a + b) / 2
            a, b = (mid, b) if at_least(mid) < alpha / 2 else (a, mid)
        low = (a + b) / 2
    if hits < total:
        a, b = 0.0, 1.0
        for _ in range(120):
            mid = (a + b) / 2
            a, b = (mid, b) if at_most(mid) > alpha / 2 else (a, mid)
        high = (a + b) / 2
    return low, high


def in_batch(name: str, scenario_id: str) -> bool:
    """Batch membership: the scenario's own id followed by a three-digit seed.

    A looser `-\\d{3}$` looked right and quietly admitted `r3-aborted-529`,
    whose name ends in three digits by coincidence. Naming is not a data model;
    the id has to match too. Arm runs carry `-armb`/`-armc` before the seed,
    since the arm is part of a run's identity and mixing arms under one name
    would be unreadable afterwards.
    """
    return re.fullmatch(rf"{re.escape(scenario_id)}(-arm[bc])?-\d{{3}}",
                        name) is not None


def load(runs: Path, everything: bool) -> list[dict]:
    """Regrade each run. Never reads the `verdict.json` sitting beside it.

    Those files are written once, by whichever grader was current when the run
    landed, and the first draft of this script folded a pre-criterion-1-gate
    verdict straight into a fresh batch table. Batch membership is by directory
    name — pilots and aborted shells are not part of a batch and are excluded
    unless asked for.
    """
    grader = importlib.util.spec_from_file_location("replay_grade",
                                                    HERE / "grade.py")
    module = importlib.util.module_from_spec(grader)
    grader.loader.exec_module(module)

    reports = []
    for meta in sorted(runs.glob("*/meta.json")):
        name = meta.parent.name
        if not everything:
            try:
                scenario_id = json.loads(meta.read_text(encoding="utf-8"))["id"]
            except (json.JSONDecodeError, KeyError):
                continue
            if not in_batch(name, scenario_id):
                continue
        report = module.grade(meta.parent)
        report["_dir"] = name
        try:
            report["_surface"] = json.loads(
                meta.read_text(encoding="utf-8")).get("surface")
        except json.JSONDecodeError:
            report["_surface"] = None
        reports.append(report)
    return reports


def summarise(reports: list[dict]) -> dict:
    scenarios: dict[str, dict] = {}
    for report in reports:
        key = report["scenario"]
        if report.get("arm", "a") != "a":
            key = f"{key} [arm {report['arm'].upper()}]"
        row = scenarios.setdefault(key, {
            "runs": [], "correct": 0, "incorrect": 0, "invalid": 0,
            "faults": 0, "unreconciled": 0,
            "bookkeeping_runs": 0, "bookkeeping_ok": 0})
        row["runs"].append(report["_dir"])
        row.setdefault("surfaces", set()).add(report.get("_surface"))
        row[report["verdict"]] += 1
        row["faults"] += report.get("provider_faults", {}).get("seen", 0)
        third = report.get("criterion_3", {})
        row["unreconciled"] += third.get("unreconciled", 0)
        if third.get("had_bookkeeping_to_do"):
            row["bookkeeping_runs"] += 1
            row["bookkeeping_ok"] += 1 if third.get("reconciled") else 0

    for name, row in scenarios.items():
        valid = row["correct"] + row["incorrect"]
        low, high = clopper_pearson(row["correct"], valid)
        row["valid"] = valid
        row["rate"] = (row["correct"] / valid) if valid else None
        row["ci95"] = [round(low, 3), round(high, 3)]
        row["surfaces"] = sorted(x for x in row.get("surfaces", set()) if x)

    # r2 is scored per turn, and turns inside one run are not independent. The
    # pre-registered reading is the per-turn lapse rate plus where the first
    # lapse falls, so both are produced; the concentration of lapses on one
    # turn index is the thing to look at before any talk of decay.
    # Grouped by scenario, never pooled. `r2b` exists only to be compared
    # against `r2`, and a per-turn table that averaged the two would answer
    # neither question — the manipulation would be diluted by its own control.
    per_turn: dict[str, dict] = {}
    for report in reports:
        name = report["scenario"]
        if not name.startswith(("r2-", "r2b-", "r2c-", "m1-", "m2-")):
            continue
        row = per_turn.setdefault(name, {"reached": Counter(), "lapsed": Counter(),
                                         "tabled": Counter(), "first_lapse": []})
        outcome = report["outcome"]
        for index in outcome.get("turns_reached", []):
            row["reached"][index] += 1
        for index in outcome.get("turns_without_decision_line", []):
            row["lapsed"][index] += 1
        for index in outcome.get("turns_with_consequence_table", []):
            row["tabled"][index] += 1
        row["first_lapse"].append(outcome.get("first_lapse"))

    return {"scenarios": scenarios,
            "per_turn": {name: {key: (dict(sorted(value.items()))
                                      if isinstance(value, Counter) else value)
                                for key, value in row.items()}
                         for name, row in sorted(per_turn.items())}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=HERE / "runs")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true",
                        help="include pilots and aborted runs, which are "
                             "not part of any batch")
    args = parser.parse_args()

    reports = load(args.runs, args.all)
    if not reports:
        raise SystemExit(f"no graded runs under {args.runs}")
    report = summarise(reports)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(f"{'scenario':<28} {'correct':>8} {'valid':>6} {'invalid':>8} "
          f"{'rate':>6}  {'exact 95% CI':<16} {'529s':>5}  {'crit3':<7} surface")
    for name, row in sorted(report["scenarios"].items()):
        rate = "—" if row["rate"] is None else f"{row['rate']:.0%}"
        span = f"[{row['ci95'][0]:.3f}, {row['ci95'][1]:.3f}]"
        marks = sorted(x for x in row.get("surfaces", set()) if x)
        stamp = ",".join(marks) if marks else "unrecorded"
        print(f"{name:<28} {row['correct']:>8} {row['valid']:>6} "
              f"{row['invalid']:>8} {rate:>6}  {span:<16} {row['faults']:>5} "
              f"{row['bookkeeping_ok']}/{row['bookkeeping_runs']:<6} {stamp}")

    for name, row in report["per_turn"].items():
        print(f"\n{name}, per turn (unit is the turn; turns within a run are "
              "not independent)")
        for index in sorted(row["reached"]):
            print(f"  turn {index}: reached {row['reached'][index]}, "
                  f"no DECISION line {row['lapsed'].get(index, 0)}, "
                  f"consequence table {row['tabled'].get(index, 0)}")
        print(f"  first lapse per run: {row['first_lapse']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
