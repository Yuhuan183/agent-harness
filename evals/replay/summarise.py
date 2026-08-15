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
from itertools import combinations
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


def rank_separation(left: list[float], right: list[float]) -> dict:
    """Exact two-sided Mann-Whitney, and whether the two ranges touch at all.

    Computed here rather than imported, for the reason the interval above is:
    a number a reader will cite has to come from something they can re-run.

    Both figures are printed because at n=5 per arm they are nearly the same
    fact — complete separation is the only configuration that reaches p < 0.05 —
    and the overlap is the half a reader can check by eye against the values on
    the line above. A p-value alone would ask them to trust the arithmetic.

    Exact by enumeration, which is why it refuses rather than approximates past
    a bounded size: a summary that silently switched to a normal approximation
    at some batch size would change what its own numbers mean without saying so.
    """
    n_left, n_right = len(left), len(right)
    if not n_left or not n_right:
        return {"comparable": False, "why": "an arm has no runs"}
    if n_left + n_right > 20:
        return {"comparable": False,
                "why": f"exact enumeration is bounded at 20 runs, got "
                       f"{n_left + n_right}"}

    def statistic(xs, ys):
        return sum(1.0 if x > y else 0.5 if x == y else 0.0
                   for x in xs for y in ys)

    pooled = list(left) + list(right)
    observed = statistic(left, right)
    extreme = min(observed, n_left * n_right - observed)
    hits = total = 0
    for pick in combinations(range(len(pooled)), n_left):
        chosen = set(pick)
        one = [pooled[i] for i in pick]
        two = [pooled[i] for i in range(len(pooled)) if i not in chosen]
        value = statistic(one, two)
        total += 1
        if min(value, n_left * n_right - value) <= extreme:
            hits += 1
    return {"comparable": True, "p_two_sided": hits / total,
            "ranges_disjoint": max(left) < min(right) or max(right) < min(left)}


def in_batch(name: str, scenario_id: str) -> bool:
    """Batch membership: the scenario's own id followed by a three-digit seed.

    A looser `-\\d{3}$` looked right and quietly admitted `r3-aborted-529`,
    whose name ends in three digits by coincidence. Naming is not a data model;
    the id has to match too. Arm runs carry `-armb`/`-armc` before the seed,
    since the arm is part of a run's identity and mixing arms under one name
    would be unreadable afterwards.
    """
    return re.fullmatch(rf"{re.escape(scenario_id)}(-arm[bcs])?-\d{{3}}",
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
        if not name.startswith(("r2-", "r2b-", "r2c-", "m1-", "m2-", "m3-")):
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

    # A scored scenario needs its distribution shown, not its pass rate. `q1`
    # exists because `r3` came back 5 of 5 and a criterion on its ceiling cannot
    # show a contract clause being worth anything; printing `0%` for four runs
    # that each got ten of eleven right would repeat that mistake from the other
    # end. The per-clause tally underneath is the instrument's own check: a
    # clause that most runs of the *reference* arm get "wrong" is more likely a
    # bad key than a bad run, and that has to be visible before any arm is
    # compared against another.
    quality: dict[str, dict] = {}
    for report in reports:
        outcome = report["outcome"]
        if "label_score" not in outcome:
            continue
        name = report["scenario"]
        if report.get("arm", "a") != "a":
            name = f"{name} [arm {report['arm'].upper()}]"
        row = quality.setdefault(name, {"items": outcome["items"], "scores": [],
                                        "pairs": [], "leaves": [],
                                        "leaves_unattributable": 0,
                                        "leaves_saw_both": 0,
                                        "excluded_invalid": 0,
                                        "wrong_by_clause": Counter()})
        if report["verdict"] == "invalid":
            row["excluded_invalid"] += 1
            continue
        row["scores"].append(outcome["label_score"])
        row["pairs"].append(outcome["conflict_pairs_correct"])
        coverage = outcome.get("leaf_coverage") or {}
        for leaf in coverage.get("reports", []):
            if leaf.get("document"):
                row["leaves"].append(f"{leaf['named']}/{leaf['of']}")
        row["leaves_unattributable"] += len(coverage.get("unattributable") or [])
        row["leaves_saw_both"] += len(coverage.get("saw_both") or [])
        for clause, given in outcome["wrong_labels"].items():
            row["wrong_by_clause"][f"{clause} -> {given}"] += 1
    for row in quality.values():
        row["mean"] = (sum(row["scores"]) / len(row["scores"])
                       if row["scores"] else None)
        row["wrong_by_clause"] = dict(row["wrong_by_clause"].most_common())

    # `q2` is scored on recall of planted contradictions, and its shape columns
    # are half the point: the request does not say how to work, so how the
    # session chose to work is data. Shape and score are printed together
    # because the pre-registered reading needs both — a difference in recall
    # with no difference in shape means something other than the dispatch moved.
    unstated: dict[str, dict] = {}
    for report in reports:
        outcome = report["outcome"]
        if "recall" not in outcome:
            continue
        name = report["scenario"]
        if report.get("arm", "a") != "a":
            name = f"{name} [arm {report['arm'].upper()}]"
        row = unstated.setdefault(name, {"planted": outcome["planted"],
                                         "recall": [], "false_pairs": [],
                                         "invented": [], "dispatched": [],
                                         "isolated": 0, "held_both": 0,
                                         "excluded_invalid": 0,
                                         "missed_by_pair": Counter()})
        if report["verdict"] == "invalid":
            row["excluded_invalid"] += 1
            continue
        shape = outcome["shape"]
        row["recall"].append(outcome["recall"])
        row["false_pairs"].append(outcome["false_pairs"])
        row["invented"].append(outcome["invented"])
        row["dispatched"].append(shape["dispatched"])
        row["isolated"] += 1 if shape["isolated"] else 0
        row["held_both"] += shape["leaves_both_documents"]
        for pair in outcome["missed"]:
            row["missed_by_pair"][" x ".join(pair)] += 1
    for row in unstated.values():
        row["mean_recall"] = (sum(row["recall"]) / len(row["recall"])
                              if row["recall"] else None)
        row["missed_by_pair"] = dict(row["missed_by_pair"].most_common())

    # A scenario with a continuous compliance measure is compared on that
    # measure, never on its pass rate. The threshold that turns 84 Han
    # characters into `in_chinese: True` throws away precisely what a
    # sensitivity question needs: a weakened clause that halves the Chinese in
    # a reply still scores 5 of 5 on the binary and is invisible, while the
    # counts separate cleanly. Same runs, same cost — at n=5 the binary
    # resolves a shift of about 80%, the counts about 10%.
    dose: dict[str, dict] = {}
    for report in reports:
        outcome = report["outcome"]
        if "han_characters" not in outcome:
            continue
        row = dose.setdefault(report["scenario"], {})
        arm = report.get("arm", "a").upper()
        cell = row.setdefault(arm, {"han": [], "latin": [], "invalid": 0})
        if report["verdict"] == "invalid":
            cell["invalid"] += 1
            continue
        cell["han"].append(outcome["han_characters"])
        cell["latin"].append(outcome["latin_letters"])
    for row in dose.values():
        reference = row.get("A", {}).get("han") or []
        for arm, cell in row.items():
            cell["mean"] = (sum(cell["han"]) / len(cell["han"])
                            if cell["han"] else None)
            cell["against_a"] = (
                rank_separation(reference, cell["han"])
                if arm != "A" and reference and cell["han"] else None)

    return {"scenarios": scenarios,
            "quality": quality,
            "unstated": unstated,
            "dose": dose,
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

    for name, row in sorted(report.get("quality", {}).items()):
        mean = "—" if row["mean"] is None else f"{row['mean']:.2f}"
        print(f"\n{name}, scored sheets (unit is the run; the number to compare "
              "across arms is the mean, not the pass rate)")
        print(f"  labels right: {row['scores']} of {row['items']}, "
              f"mean {mean}")
        print(f"  conflict pairs right: {row['pairs']} of 2 "
              f"({row['excluded_invalid']} invalid run(s) excluded)")
        if row["leaves"]:
            full = sum(1 for cell in row["leaves"]
                       if cell.split("/")[0] == cell.split("/")[1])
            print(f"  leaf reports naming their own document's clauses: "
                  f"{row['leaves']} — {full} of {len(row['leaves'])} complete")
        # Printed even at zero. A denominator that shrinks in silence is the
        # thing this line exists to prevent.
        print(f"  leaves unattributable: {row['leaves_unattributable']}, "
              f"holding both documents: {row['leaves_saw_both']}")
        for clause, count in row["wrong_by_clause"].items():
            print(f"  missed: {clause} ({count})")

    for name, row in sorted(report.get("unstated", {}).items()):
        mean = "—" if row["mean_recall"] is None else f"{row['mean_recall']:.2f}"
        runs = len(row["recall"])
        print(f"\n{name}, planted contradictions found (the request never said "
              "how to work, so the shape below is data, not a marker)")
        print(f"  recall: {row['recall']} of {row['planted']}, mean {mean}")
        print(f"  claimed a near miss: {row['false_pairs']}, "
              f"invented a pair: {row['invented']}")
        print(f"  dispatched: {row['dispatched']} — isolated {row['isolated']} "
              f"of {runs}, leaves holding both documents {row['held_both']} "
              f"({row['excluded_invalid']} invalid run(s) excluded)")
        for pair, count in row["missed_by_pair"].items():
            print(f"  missed: {pair} ({count})")

    for name, row in sorted(report.get("dose", {}).items()):
        print(f"\n{name}, compliance by count (compare these, not the pass "
              "rate: the binary resolves ~80% at n=5, the counts ~10%)")
        for arm in sorted(row):
            cell = row[arm]
            mean = "—" if cell["mean"] is None else f"{cell['mean']:.1f}"
            span = (f"{min(cell['han'])}-{max(cell['han'])}" if cell["han"]
                    else "—")
            print(f"  arm {arm}  han {cell['han']}  mean {mean}  range {span}"
                  f"  (latin {cell['latin']})")
        for arm in sorted(row):
            against = row[arm].get("against_a")
            if not against:
                continue
            if not against["comparable"]:
                print(f"  A vs {arm}: not compared — {against['why']}")
            else:
                print(f"  A vs {arm}: exact two-sided p = "
                      f"{against['p_two_sided']:.4f}, ranges "
                      f"{'disjoint' if against['ranges_disjoint'] else 'overlap'}")

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
