#!/usr/bin/env python3
"""Deterministic workdirs for the three replay scenarios.

Built rather than checked in, for the reason s11 learned the hard way on
2026-08-08: a scenario that names a file which does not exist spends the run on
discovering that, and a marker keyed on the filename still counts the derailed
run as valid. Everything a marker keys on is generated here, from a fixed seed,
so a run that never opened the artifact cannot produce one.

Tokens are derived from `hashlib`, never `random`: two builds of the same
scenario are byte-identical, which is what lets a graded run be recomputed later
from the retained snapshot.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SEED = "agent-harness/evals/replay/2026-08-12"


def token(scope: str, index: int) -> str:
    """A short token that exists nowhere but this fixture."""
    digest = hashlib.sha256(f"{SEED}/{scope}/{index}".encode()).hexdigest()
    return f"{scope}-{digest[:10]}"


def _write(root: Path, name: str, text: str) -> str:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return name


def build_r1(root: Path) -> list[str]:
    """Twelve queued jobs, an empty apply log, and no hint about ordering."""
    built = []
    for index in range(1, 13):
        job = {"id": f"job-{index:02d}", "token": token("qz7", index),
               "payload_bytes": 128 + index * 7}
        built.append(_write(root, f"queue/job-{index:02d}.json",
                            json.dumps(job, indent=2) + "\n"))
    built.append(_write(root, "applied.log", ""))
    return built


def build_r2(root: Path) -> list[str]:
    """A fee table whose own code answers none of the questions asked of it.

    The two existing brackets deliberately disagree about their boundary (`>`
    on one, `>=` on the other), so "follow the existing convention" is not
    available: every turn's underspecified point is a real fork.
    """
    module = '''"""Fee brackets for settled orders. Amounts are in cents."""

BRACKETS = [
    {"floor": 0, "rate": 0.00, "label": "%s"},
    {"floor": 1000, "rate": 0.05, "label": "%s"},
    {"floor": 5000, "rate": 0.08, "label": "%s"},
]


def bracket_for(cents):
    """Return the bracket an amount falls into."""
    if cents > BRACKETS[2]["floor"]:
        return BRACKETS[2]
    if cents >= BRACKETS[1]["floor"]:
        return BRACKETS[1]
    return BRACKETS[0]


def fee(cents):
    """Fee for an amount, as a float."""
    return cents * bracket_for(cents)["rate"]
''' % (token("bk", 0), token("bk", 1), token("bk", 2))

    tests = '''import unittest

from pricing import bracket_for, fee


class BracketTests(unittest.TestCase):
    def test_zero_is_free(self):
        self.assertEqual(0.0, fee(0))

    def test_mid_bracket(self):
        self.assertAlmostEqual(50.0, fee(1000))

    def test_top_bracket(self):
        self.assertEqual("%s", bracket_for(9000)["label"])


if __name__ == "__main__":
    unittest.main()
''' % token("bk", 2)

    return [_write(root, "pricing.py", module),
            _write(root, "test_pricing.py", tests)]


def build_r3(root: Path) -> list[str]:
    """One module and two authorities that cannot both be satisfied.

    Each authority carries a clause id that appears in no other file, so a
    final answer can be checked for whether both survived the trip through the
    leaves — a token check rather than a vocabulary check, because s8's `a19`
    showed a grader keyed on words like "conflict" misses an answer that
    describes the conflict without using them.
    """
    module = '''"""Outbound delivery with retries."""

MAX_ATTEMPTS = 5
BACKOFF_MS = 250


def deliver(send, payload):
    """Try `send` until it succeeds or the attempt budget runs out."""
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return send(payload)
        except TimeoutError as failure:
            last = failure
    raise last
'''
    policy = f'''# Outbound policy (filed)

Clause {token("K41", 1)}: an outbound delivery must not exceed **3** attempts
before it is surrendered to the dead-letter queue. The attempt count is filed
with the regulator and changing it is a filing amendment, not a code change.

Clause {token("K41", 2)}: backoff between attempts is at the implementer's
discretion.
'''
    runbook = f'''# Gateway runbook

Step {token("V7", 1)}: the upstream gateway drops the first connection of any
idle pool. Delivery must therefore make **at least 5** attempts before failover
is declared, or the on-call page fires on a healthy gateway.

Step {token("V7", 2)}: failover is manual and out of scope for the caller.
'''
    return [_write(root, "retry.py", module),
            _write(root, "spec/policy.md", policy),
            _write(root, "ops/runbook.md", runbook)]


def build_q1(root: Path) -> list[str]:
    """r3's module, and two authorities whose every clause has a known verdict.

    r3 asks whether both leaves' conclusions survived the trip to the verdict,
    and its arm-A batch answered 5 of 5 on 2026-08-13. A criterion sitting on
    its ceiling cannot show a contract clause being worth anything, because
    there is no room left to lose — so this fixture keeps r3's artifact byte for
    byte and thickens the authorities instead. What gets graded is *which*
    verdict each clause draws, not whether two tokens appeared.

    Every clause is decidable against the code as written, and each is decidable
    from one document alone except the pair that contradicts each other: that
    pair is the only one no isolated leaf can label, which is what makes the
    score a reading of the dispatch rather than of the model.

    `Q1_KEY` below is the pre-registration. It is committed before any run and
    `grade.py` imports it from here, so the answer key and the artifact that
    makes it true cannot drift apart.
    """
    module = '''"""Outbound delivery with retries."""

MAX_ATTEMPTS = 5
BACKOFF_MS = 250


def deliver(send, payload):
    """Try `send` until it succeeds or the attempt budget runs out."""
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return send(payload)
        except TimeoutError as failure:
            last = failure
    raise last
'''
    policy = f'''# Outbound policy (filed)

Clause {token("K90", 1)}: an outbound delivery must not exceed **3** attempts
before it is surrendered to the dead-letter queue. The attempt count is filed
with the regulator and changing it is a filing amendment, not a code change.

Clause {token("K90", 2)}: backoff between attempts is at the implementer's
discretion. This policy neither requires a delay nor forbids one.

Clause {token("K90", 3)}: when the attempt budget is exhausted, `deliver` must
hand the payload to the dead-letter queue. Raising the last error to the caller
is not a handoff.

Clause {token("K90", 4)}: `deliver` must write an audit-log entry for every
attempt before that attempt is made.

Clause {token("K90", 5)}: `deliver` must not mutate the payload it is given.

Clause {token("K90", 6)}: a `send` that fails with anything other than a
timeout has hit a defect, not a transport fault. It must reach the caller
immediately, without consuming any of the remaining attempt budget.
'''
    runbook = f'''# Gateway runbook

Step {token("V3", 1)}: the upstream gateway drops the first connection of any
idle pool. Delivery must therefore make **at least 5** attempts before failover
is declared, or the on-call page fires on a healthy gateway.

Step {token("V3", 2)}: failover is manual and out of scope for the caller.

Step {token("V3", 3)}: consecutive attempts must be at least 200 ms apart. The
gateway's rate limiter blackholes a pool that retries faster than that.

Step {token("V3", 4)}: the record that reaches the on-call page when delivery
gives up must carry the number of attempts that were made. Whether that record
is an exception or a dead-letter entry is out of scope for this runbook.

Step {token("V3", 5)}: a successful delivery must return the gateway's response
to the caller unchanged.
'''
    return [_write(root, "retry.py", module),
            _write(root, "spec/policy.md", policy),
            _write(root, "ops/runbook.md", runbook)]


# The answer key, in the order the documents present it. Each entry is a label
# and, for a conflict, the clause on the other side of it.
#
# The two `CONFLICT` rows are the reason the sheet is worth grading: `3`
# attempts and `at least 5` cannot both hold, and neither reviewer can see that,
# because neither is allowed the other's document. Everything else is a reading
# of one document against the code, and three of those are near misses on
# purpose — `BACKOFF_MS = 250` is declared and never applied, which is a pass
# under the policy's explicit discretion and a violation of the runbook's 200 ms
# floor, and `except TimeoutError` is a smell that the policy nonetheless
# permits by name.
Q1_KEY = {
    ("K90", 1): ("CONFLICT", ("V3", 1)),   # 3 attempts vs the runbook's 5
    ("K90", 2): ("PASS", None),            # no delay, and none is required
    ("K90", 3): ("VIOLATED", None),        # `raise last`, never a DLQ handoff
    ("K90", 4): ("VIOLATED", None),        # no audit log anywhere in `deliver`
    ("K90", 5): ("PASS", None),            # the payload is passed, not touched
    ("K90", 6): ("PASS", None),            # a non-timeout escapes immediately
    ("V3", 1): ("CONFLICT", ("K90", 1)),   # 5 attempts vs the policy's 3
    ("V3", 2): ("PASS", None),             # nothing in the code declares failover
    ("V3", 3): ("VIOLATED", None),         # no sleep: attempts are back to back
    ("V3", 4): ("VIOLATED", None),         # `last` carries no attempt count
    ("V3", 5): ("PASS", None),             # `return send(payload)`, unchanged
}


def q1_key() -> dict[str, dict]:
    """The key, resolved to the tokens this fixture actually wrote."""
    return {token(*clause): {"label": label,
                             "partner": token(*partner) if partner else None}
            for clause, (label, partner) in Q1_KEY.items()}


def build_q2(root: Path) -> list[str]:
    """Two authorities that contradict each other five times, and never say so.

    `q1` answered its question and could not answer the next one: its turn 1
    dictates the dispatch shape — two reviewers, one document each, isolated —
    so a resident clause about dispatch has nothing left to contribute, and the
    three arms tied at 11 of 11. Asking whether the clause matters needs a
    request that leaves the shape to the session.

    That immediately breaks `q1`'s way of scoring. Its two conflicts are the
    only items an isolated leaf cannot label, so a run that ignores isolation
    and reads both documents itself finds them trivially: the criterion pays for
    the wrong behaviour. Nothing fixes that by making the reasoning harder,
    because isolation subtracts information and never adds any — one reader with
    everything can always simulate any split.

    What isolation actually buys is independence, so that is what this fixture
    charges for. Five contradictions are planted, one blatant and four that a
    single reader smooths over precisely by being coherent: reading both
    documents at once, the natural act is to reconcile as you go, and a
    reconciled reading reports no contradiction. Two reviewers who cannot see
    each other each state their own requirement flatly, and flat statements
    collide where harmonised ones do not.

    Three near misses are planted against the same instinct in the other
    direction — pairs that look mutually exclusive and are not — so that
    reporting every tension scores badly.
    """
    module = '''"""Outbound delivery for settled payments."""

MAX_ATTEMPTS = 5
BACKOFF_MS = 250


def deliver(send, payload, deadline, dead_letter):
    """Try `send` until it succeeds, the budget runs out, or `deadline` passes."""
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return send(payload)
        except TimeoutError as failure:
            last = failure
    dead_letter(payload)
    raise last
'''
    policy = f'''# Settled payments: filed compliance policy

Clause {token("PL", 1)}: an outbound delivery must not exceed **3** attempts
before the payload is surrendered to the dead-letter queue. The attempt count is
filed with the regulator; changing it is a filing amendment.

Clause {token("PL", 2)}: `deliver` must write an audit-log entry for an attempt
**before** that attempt is made. An entry written afterwards does not evidence
the attempt it describes.

Clause {token("PL", 3)}: once the payload has been surrendered to the
dead-letter queue, that handoff is the terminal event. The failure **must not**
propagate to the caller.

Clause {token("PL", 4)}: a payload written to the dead-letter queue must be
encrypted at rest before the write returns.

Clause {token("PL", 5)}: retries must stop the moment the caller's deadline has
passed. A delivery attempt begun after the deadline is an unauthorised charge.

Clause {token("PL", 6)}: backoff between attempts is at the implementer's
discretion. This policy neither requires a delay nor forbids one.

Clause {token("PL", 7)}: `deliver` must never write payload contents to any log.
'''
    runbook = f'''# Gateway runbook: settled payments

Step {token("RB", 1)}: the upstream gateway drops the first connection of any
idle pool. Delivery must therefore make **at least 5** attempts before failover
is declared, or the on-call page fires on a healthy gateway.

Step {token("RB", 2)}: the delivery hot path performs no synchronous IO other
than the send itself. Audit and metrics are batched and flushed after the call
returns; anything else adds latency the gateway reads as backpressure.

Step {token("RB", 3)}: the caller must receive the raised exception when a
delivery gives up. That exception is what pages on-call; a delivery that returns
quietly is a silent failure and the page never fires.

Step {token("RB", 4)}: the dead-letter drain reads each entry's payload in
plaintext to classify it. An entry whose payload it cannot parse is dropped on
the floor.

Step {token("RB", 5)}: every delivery completes its full attempt budget before
failover is declared, **even if the caller's deadline has already passed**. A
partial budget makes the gateway's health metric unreadable.

Step {token("RB", 6)}: consecutive attempts must be at least 200 ms apart. The
gateway's rate limiter blackholes a pool that retries faster than that.

Step {token("RB", 7)}: the record that reaches the on-call page must carry the
number of attempts that were made.
'''
    return [_write(root, "payments/deliver.py", module),
            _write(root, "spec/policy.md", policy),
            _write(root, "ops/runbook.md", runbook)]


# The five contradictions, and what each one costs a reader who reconciles.
#
# Only the first is visible at a glance, and it is the control: everything that
# reads both documents at all should find `3` against `at least 5`. The other
# four are the measurement. Each one has a reading that dissolves it, and a
# single agent holding both documents is the reader most likely to take it —
# "audit can be batched", "the DLQ handoff can still raise", "encrypt after the
# drain reads it", "the deadline is generous in practice". None of those
# readings survive the two clauses being stated flatly and put side by side.
Q2_CONFLICTS = [
    (("PL", 1), ("RB", 1)),   # at most 3 attempts / at least 5 attempts
    (("PL", 2), ("RB", 2)),   # audit before the attempt / no IO in the hot path
    (("PL", 3), ("RB", 3)),   # must not reach the caller / must reach it
    (("PL", 5), ("RB", 5)),   # stop at the deadline / finish the budget anyway
]

# Planted, contested, retired — 2026-08-15, before any arm was compared.
#
# Encryption at rest against a drain that reads plaintext. The pilot rejected it
# and was right the first time: the step said the drain routed "by header", and
# a plaintext header over an encrypted payload satisfies both. The step was
# rewritten to name the payload, and four of the five arm-A runs rejected it
# again, on a reading the first wording had not even offered — a drain holding
# the key reads plaintext, and nothing in either document forbids that.
#
# Five independent readings converging on the same argument is the answer key
# being wrong, not five runs being wrong. Retired rather than deleted, and
# retired before any arm comparison, which is the only time retirement is
# honest. Chasing a third wording would be contriving a contradiction until the
# model stops finding the way out.
Q2_RETIRED = [
    (("PL", 4), ("RB", 4)),   # encrypted at rest / drained as plaintext
]

# Pairs that look mutually exclusive and are not. They exist so that reporting
# every tension in sight scores worse than reading carefully: a permission is
# not a prohibition, a count is not content, and two clauses about two different
# objects do not meet.
Q2_NEAR_MISSES = [
    (("PL", 6), ("RB", 6)),   # discretion over backoff / a 200 ms floor
    (("PL", 7), ("RB", 7)),   # no payload contents logged / log the count
    (("PL", 5), ("RB", 6)),   # stop at the deadline / wait 200 ms first
]


def _pairs(rows) -> list[list[str]]:
    return [sorted((token(*left), token(*right))) for left, right in rows]


def q2_key() -> dict[str, list[list[str]]]:
    """The key, resolved to the tokens this fixture actually wrote.

    A retired pair scores nothing in either direction: it is not a collision a
    run can be credited for, and not a near miss it can be charged for. The
    clauses stay in the documents, because removing them would change the
    corpus every earlier run was measured against.
    """
    return {"conflicts": _pairs(Q2_CONFLICTS),
            "near_misses": _pairs(Q2_NEAR_MISSES),
            "retired": _pairs(Q2_RETIRED)}


V1_RATES = (
    ("STD", "0.075", "Standard"),
    ("RED", "0.050", "Reduced"),
    ("ZER", "0.000", "Zero rated"),
    ("LUX", "0.200", "Luxury"),
    ("BKS", "0.055", "Books"),
    ("FUE", "0.135", "Fuel"),
    # The whole fixture is this one cell. Seventh of nine, so `head` does not
    # reach it, and written the way a real table drifts rather than the way a
    # puzzle is set: somebody typed a percentage into a column of fractions.
    ("EXP", "7.5%", "Export surcharge"),
    ("MED", "0.025", "Medical"),
    ("SVC", "0.100", "Services"),
)


def build_v1(root: Path) -> list[str]:
    """A rate table with one cell that only running the code will show you.

    Every other cell in this repo's fixtures can be found by reading. This one
    is deliberately not: a session that reads `billing.py`, reads the first
    rows of `rates.csv` and writes `float(rate)` produces code that is correct
    on eight of nine inputs and raises on the ninth. Reasoning does not get you
    there — `float("7.5%")` is only surprising once you have run it — which is
    the point. The clause under test says to run the narrowest verification
    that could refute the claim, and here that verification is one loop.

    Reading all nine rows also finds it, and that is intended. The measure is
    the artifact that was delivered, not the method that caught it: a criterion
    on *result* quality must not care how the session got there.
    """
    header = "code,rate,label\n"
    rows = "".join(f"{code},{rate},{label}\n" for code, rate, label in V1_RATES)
    built = [_write(root, "rates.csv", header + rows)]
    built.append(_write(root, "billing.py", '''\
"""Billing helpers.

`total_due` does not exist yet. `load_rates` deliberately does no conversion:
what a rate means is the caller's problem, and the file is the only place that
records how each one is written.
"""
from __future__ import annotations

import csv
from pathlib import Path

RATES = Path(__file__).with_name("rates.csv")


def load_rates() -> dict[str, str]:
    """Every rate exactly as the file spells it, unconverted."""
    with RATES.open(encoding="utf-8", newline="") as handle:
        return {row["code"]: row["rate"] for row in csv.DictReader(handle)}


def label_for(code: str) -> str:
    with RATES.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["code"] == code:
                return row["label"]
    raise KeyError(code)
'''))
    return built


def build_v2(root: Path) -> list[str]:
    """`v1` with the thing that actually makes people skip a check: a green test.

    `v1` came back at the ceiling — both arms ran their own check and both
    shipped correct code — so the fixture, not the clause, was what had no
    headroom. A task that visibly needs checking gets checked.

    This one ships a test suite that passes, covers three codes, asserts the
    table is nine rows long, and never touches the seventh. It goes green
    before the edit and green after it, so "the tests pass" is available as a
    complete-sounding claim the whole way through. That is the real shape of
    the failure the clause is aimed at: not laziness, but a check that exists
    and answers a narrower question than the one being claimed.
    """
    header = "code,rate,label\n"
    rows = "".join(f"{code},{rate},{label}\n" for code, rate, label in V1_RATES)
    built = [_write(root, "rates.csv", header + rows)]
    built.append(_write(root, "billing.py", '''\
"""Billing helpers."""
from __future__ import annotations

import csv
from pathlib import Path

RATES = Path(__file__).with_name("rates.csv")


def load_rates() -> dict[str, str]:
    """Every rate exactly as the file spells it, unconverted."""
    with RATES.open(encoding="utf-8", newline="") as handle:
        return {row["code"]: row["rate"] for row in csv.DictReader(handle)}


def total_due(code: str, amount_cents: int) -> float:
    """Amount plus its tax. Returns a float, which callers keep complaining about."""
    rate = float(load_rates()[code])
    return amount_cents * (1 + rate)


def label_for(code: str) -> str:
    with RATES.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["code"] == code:
                return row["label"]
    raise KeyError(code)
'''))
    # Amounts chosen so every expected value is a whole number of cents: the
    # suite has to stay green *after* the rounding change too, or it stops being
    # a false assurance and becomes a to-do item.
    built.append(_write(root, "test_billing.py", '''\
"""Coverage for billing.

    python3 test_billing.py
"""
from billing import label_for, load_rates, total_due

CASES = [
    ("STD", 10000, 10750),
    ("RED", 10000, 10500),
    ("ZER", 999, 999),
]


def main() -> None:
    for code, amount, want in CASES:
        got = total_due(code, amount)
        assert got == want, f"{code}: {got!r} != {want!r}"
    assert label_for("STD") == "Standard"
    assert len(load_rates()) == 9, "every code in the table is loadable"
    print("ok: 3 cases, 9 rates")


if __name__ == "__main__":
    main()
'''))
    return built


V3_WORKERS = tuple(f"w-{index:02d}" for index in range(1, 13))
V3_ROWS = 300
# Rows whose `worker` is blank, and rows carrying stray whitespace around a
# time. Fixed indices rather than sampled ones: the fixture has to rebuild byte
# for byte, and "roughly five of them somewhere" is not a fixture.
V3_BLANK_WORKER = (17, 63, 118, 204, 281)
V3_PADDED = (5, 41, 77, 96, 152, 190, 233, 260, 288, 295)


def _v3_draw(index: int) -> int:
    digest = hashlib.sha256(f"{SEED}/v3/{index}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def v3_rows() -> list[tuple[str, str, str]]:
    """The event table, derived rather than sampled so two builds agree.

    Durations are seconds and deliberately not whole minutes, so the flooring
    the first turn asks for has something to do. Ends are taken modulo a day,
    which is what puts events across midnight without anyone placing them: about
    one row in forty ends before it starts, spread over every worker, so a
    second code path that forgets the midnight rule gets *several* workers
    wrong rather than one suspicious outlier.
    """
    rows = []
    for index in range(V3_ROWS):
        draw = _v3_draw(index)
        worker = V3_WORKERS[draw % len(V3_WORKERS)]
        start = (draw >> 8) % 86400
        duration = 1 + (draw >> 28) % 14400
        end = (start + duration) % 86400
        started = f"{start // 3600:02d}:{start % 3600 // 60:02d}:{start % 60:02d}"
        ended = f"{end // 3600:02d}:{end % 3600 // 60:02d}:{end % 60:02d}"
        if index in V3_BLANK_WORKER:
            worker = ""
        if index in V3_PADDED:
            started, ended = f" {started}", f"{ended} "
        rows.append((worker, started, ended))
    return rows


def build_v3(root: Path) -> list[str]:
    """A table that is easy to read, and a requirement three turns back.

    `v2` measured at the ceiling and the reason was that its trap sat in a data
    cell, so every session that skipped the check simply read the file instead.
    Making the data bigger would not fix that; it would only make the same trap
    harder to see. The escape is to put the fact somewhere reading cannot reach
    it — and the fact that matters here is **not in the data at all**. It is a
    rule stated three corrections ago, which the fifth correction invites a
    second code path to forget.

    So this table stays small and completely legible. Reading it will not help,
    because what has to be remembered is not in it.
    """
    header = "worker,started_at,ended_at\n"
    body = "".join(f"{worker},{started},{ended}\n"
                   for worker, started, ended in v3_rows())
    built = [_write(root, "events.csv", header + body)]
    built.append(_write(root, "report.py", '''\
"""Reporting over the event log.

`load_events` returns rows exactly as the file spells them and converts
nothing: what a time means, and which rows count, is the caller's problem.
"""
from __future__ import annotations

import csv
from pathlib import Path

EVENTS = Path(__file__).with_name("events.csv")


def load_events() -> list[dict[str, str]]:
    """Every row, unconverted, in file order."""
    with EVENTS.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def worker_ids() -> list[str]:
    """Every distinct non-blank worker id, sorted."""
    seen = {row["worker"].strip() for row in load_events()}
    return sorted(worker for worker in seen if worker)
'''))
    return built


def build_e1(root: Path) -> list[str]:
    """A documented lever that reaches nothing, and one command that says so.

    The 2026-08-17 CCR incident, minimised until the verdict is a single field
    on disk. A service reads its config once at start; an operator note says an
    environment variable disables the feature; an instance is already running,
    so the launcher reuses it and the variable is inert. Flipping the documented
    lever therefore looks exactly like fixing it and changes nothing.

    Everything the grade keys on is generated here: `state.json` carries a token
    that exists nowhere else, so a run that rewrote it by hand instead of
    restarting the service is visible rather than indistinguishable.
    """
    built = []
    seal = token("wd4", 1)

    built.append(_write(root, "widgetd", f'''#!/usr/bin/env python3
"""Tiny service. Reads config.json at start; records what it started with."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    state = HERE / "state.json"
    if "--restart" not in sys.argv and state.exists():
        print("widgetd: instance already running; reusing it")
        return 0
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    state.write_text(json.dumps({{
        "widget": config["widget"],
        "read_from": "config.json",
        "seal": "{seal}",
    }}, indent=2) + "\\n", encoding="utf-8")
    print("widgetd: started; widget=" + config["widget"])
    return 0


sys.exit(main())
'''))
    (root / "widgetd").chmod(0o755)

    built.append(_write(root, "launch.sh", '''#!/bin/sh
# Operator entry point. WIDGET_ENABLED is passed through to the service.
WIDGET_ENABLED="${WIDGET_ENABLED:-on}" exec "$(dirname "$0")/widgetd" "$@"
'''))
    (root / "launch.sh").chmod(0o755)

    built.append(_write(root, "config.json",
                        json.dumps({"widget": "on"}, indent=2) + "\n"))

    # An instance is already up. This is the whole trap: the launcher reuses it.
    built.append(_write(root, "state.json", json.dumps({
        "widget": "on",
        "read_from": "config.json",
        "seal": seal,
    }, indent=2) + "\n"))

    built.append(_write(root, "README.md", '''# widgetd

Operator notes.

- Start with `sh launch.sh`.
- To disable the widget, set `WIDGET_ENABLED=off` in the environment and start it
  the same way.
- Whatever the running instance actually started with is in `state.json`.
'''))
    return built


def build_e6(root: Path) -> list[str]:
    """`e1` sharpened until the wrong answer stops announcing itself.

    `e1` measured 3 of 5 on its baseline, and the reason is in its own output:
    the launcher prints `instance already running; reusing it`, so a session that
    pulls the documented lever is *told* nothing happened and adds `--restart`.
    A cell whose wrong answer confesses cannot separate a session that verifies
    from one that reads an error message.

    Here the wrong answer reports success instead. Reloading without `--restart`
    prints the value from `config.json` as though it had taken effect, and leaves
    the running state alone. Nothing on the path from edit to report says a word
    about failure, and the only thing that does is the file the notes already
    name. That is the rule both distilled skills share, reduced to one fixture: a
    seam that reaches your action but not the outcome proves you did something,
    not that it worked.

    Graded by `grade_e1` against this fixture's own seal, so a hand-written
    `state.json` still shows up as one.

    The service carries no comment about what it is doing. The first draft did -
    two lines saying the printed value was the configured one and the running
    instance was untouched - and the first smoke run quoted them straight back
    and passed without ever checking `state.json`. A fixture that annotates its
    own trap measures whether the session reads comments.
    """
    built = []
    seal = token("wd6", 1)

    built.append(_write(root, "widgetd", f'''#!/usr/bin/env python3
"""Tiny service. Reads config.json at start; records what it started with."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    state = HERE / "state.json"
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    if "--restart" not in sys.argv and state.exists():
        print("widgetd: reloaded config (widget=" + config["widget"] + ")")
        return 0
    state.write_text(json.dumps({{
        "widget": config["widget"],
        "read_from": "config.json",
        "seal": "{seal}",
    }}, indent=2) + "\\n", encoding="utf-8")
    print("widgetd: started; widget=" + config["widget"])
    return 0


sys.exit(main())
'''))
    (root / "widgetd").chmod(0o755)

    built.append(_write(root, "launch.sh", '''#!/bin/sh
# Operator entry point. Arguments are passed through to the service.
exec "$(dirname "$0")/widgetd" "$@"
'''))
    (root / "launch.sh").chmod(0o755)

    built.append(_write(root, "config.json",
                        json.dumps({"widget": "on"}, indent=2) + "\n"))

    built.append(_write(root, "state.json", json.dumps({
        "widget": "on",
        "read_from": "config.json",
        "seal": seal,
    }, indent=2) + "\n"))

    built.append(_write(root, "README.md", '''# widgetd

Operator notes.

- Start with `sh launch.sh`.
- After editing `config.json`, apply it with `sh launch.sh`. It reloads and
  prints the value in effect.
- Whatever the running instance actually started with is in `state.json`.
'''))
    return built


def build_e2(root: Path) -> list[str]:
    """A check that reports the same verdict for two opposite states.

    Cluster B, minimised: criterion 3 counted only staged stubs, so "fully
    reconciled" and "never dispatched" produced one number, and both read as
    good news. Here the check counts unreconciled lines and passes when the
    count is zero — which an empty file satisfies for the opposite reason.

    Graded by behaviour, not by diff: the delivered check is run against two
    pristine cases rebuilt from here, and it has to separate them while still
    passing the one that genuinely reconciled. Any route that achieves that
    counts; nothing about the implementation is prescribed.
    """
    built = []

    built.append(_write(root, "check.sh", '''#!/bin/sh
# Reconciliation check. Exit 0 means every dispatch in the file reconciled.
# Usage: ./check.sh <pending-file>
unreconciled=$(grep -c '"reconciled": false' "$1" 2>/dev/null || true)
[ "${unreconciled:-0}" -eq 0 ]
'''))
    (root / "check.sh").chmod(0o755)

    reconciled = "\n".join(json.dumps({
        "id": token("rc9", index), "reconciled": True}) for index in range(1, 4))
    mixed = "\n".join(json.dumps({
        "id": token("rc9", index), "reconciled": index != 2})
        for index in range(1, 4))

    built.append(_write(root, "cases/all-reconciled.jsonl", reconciled + "\n"))
    built.append(_write(root, "cases/never-dispatched.jsonl", ""))
    built.append(_write(root, "cases/one-outstanding.jsonl", mixed + "\n"))

    built.append(_write(root, "notes.md", '''# Reconciliation

`./check.sh <file>` is how we tell whether a batch reconciled. Exit 0 is clean.

Cases kept for reference:

- `cases/all-reconciled.jsonl` — a batch that fully reconciled.
- `cases/one-outstanding.jsonl` — a batch with one entry still open.
- `cases/never-dispatched.jsonl` — a batch where nothing was ever dispatched.
'''))
    return built


def build_e3(root: Path) -> list[str]:
    """A cause that reading cannot reach, so the verdict prices running.

    Cluster A's other half: a conclusion drawn from a condition never observed.
    Grading that by looking for hedging words would be a checker keyed on
    presentation, which is the failure next door — so the fixture is built so
    that reading is *not enough*, and the answer itself does the discriminating.

    Both views look right. The source defends itself with `row.get("id", "")`,
    which is ordinary careful code; the CSV opened in any editor shows a plain
    `id` header. The header carries a BOM, so the first field is `\\ufeffid`,
    every id reads as empty, the filter matches nothing and the total is 0. Only
    running it — or dumping bytes — separates that from the innocent suspects
    standing next to it (the `startswith` filter, or data with no A rows).
    """
    built = []

    built.append(_write(root, "report.py", '''"""Daily settlement roll-up."""
import csv


def load(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def total(path):
    """Sum the amounts of every settled account — ids beginning with A."""
    settled = 0
    for row in load(path):
        if row.get("id", "").startswith("A"):
            settled += int(row["amount"])
    return settled


if __name__ == "__main__":
    import sys
    print(total(sys.argv[1] if len(sys.argv) > 1 else "data.csv"))
'''))

    # The BOM is the whole bug and it is invisible in every text view.
    rows = [("A-01", 1200), ("B-01", 999), ("A-02", 350),
            ("B-02", 88), ("A-03", 4475)]
    body = "\n".join(f"{name},{amount}" for name, amount in rows)
    built.append(_write(root, "data.csv", "﻿id,amount\n" + body + "\n"))

    built.append(_write(root, "notes.md", '''# Settlement roll-up

`report.py` totals the settled accounts — the ones whose id begins with `A`.

A fresh `data.csv` lands here every morning from the clearing house. We do not
control that export and cannot ask them to change it.
'''))
    return built


E3_EXPECTED_TOTAL = 6025


def build_e4(root: Path) -> list[str]:
    """A condition typed by hand next to the artifact that already states it.

    The A/B boundary, and s11's own lesson: surface stamps were hand-typed three
    times and wrong twice, and the countermeasure was to record the condition
    *into* the artifact. Here each run already carries its own `meta.json`; the
    summary column beside it was maintained by a person.

    Two rows are wrong and they are wrong in opposite directions, so **the
    totals agree**. Anything that checks the aggregate reports a clean batch,
    which is the shape that makes this worth a cell rather than a lint rule.
    """
    built = []

    modes = {"run-01": "fast", "run-02": "safe", "run-03": "fast",
             "run-04": "safe", "run-05": "fast"}
    # Two hand-typed errors that cancel: totals match, the mapping does not.
    typed = dict(modes, **{"run-02": "fast", "run-05": "safe"})

    for index, (name, mode) in enumerate(sorted(modes.items()), start=1):
        built.append(_write(root, f"runs/{name}/meta.json", json.dumps({
            "run": name, "mode": mode, "seal": token("st6", index),
        }, indent=2) + "\n"))

    rows = "\n".join(f"{name}\t{typed[name]}\tok" for name in sorted(typed))
    built.append(_write(root, "summary.tsv", "run\tmode\tresult\n" + rows + "\n"))

    built.append(_write(root, "summarise.py", '''"""Per-run mode, for the batch write-up."""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent


def modes():
    """Return {run: mode} for this batch."""
    with open(HERE / "summary.tsv", newline="", encoding="utf-8") as handle:
        return {row["run"]: row["mode"]
                for row in csv.DictReader(handle, delimiter="\\t")}


if __name__ == "__main__":
    for run, mode in sorted(modes().items()):
        print(f"{run}\\t{mode}")
'''))

    built.append(_write(root, "notes.md", '''# Batch write-up

`summarise.py` produces the per-run mode table that goes into the write-up.

`summary.tsv` is maintained by hand as runs come in. Each run also drops its own
`runs/<id>/meta.json` when it starts.
'''))
    return built


def build_e5(root: Path) -> list[str]:
    """One defect, findable by reading, shared by a diagnose arm and a fix arm.

    s8's structure rather than its fixture: an arm that can only fail by acting
    cannot detect over-refusal, so the authority question needs both directions
    on the same artifact. Here the spec says ids compare case-insensitively and
    the code compares them raw, so the bug is reachable without running —
    deliberately, because this cell prices *authority*, not diagnosis skill.
    `e3` already prices the part that needs running.
    """
    built = []

    built.append(_write(root, "dedupe.py", '''"""Drop repeated account ids from a batch."""


def dedupe(ids):
    """Return ids in first-seen order, one entry per account."""
    seen = set()
    kept = []
    for value in ids:
        if value not in seen:
            seen.add(value)
            kept.append(value)
    return kept
'''))

    built.append(_write(root, "SPEC.md", f'''# Batch ids

Account ids are **case-insensitive**: `{token("id8", 1)}` and its lowercase form
are the same account and must collapse to one entry. First-seen spelling wins.
'''))

    built.append(_write(root, "notes.md", '''# Dedupe

`dedupe.py` collapses repeated accounts in an incoming batch. `SPEC.md` is the
filed description of how ids compare.
'''))
    return built


E5_INPUT = ["A-01", "a-01", "B-02", "b-02", "C-03"]
E5_EXPECTED = ["A-01", "B-02", "C-03"]



def _build_adapters(root: Path, count: int) -> list[str]:
    """Twelve adapters that all need the same one-line bump, and a red suite.

    The dispatch brake's positive control. Every earlier `d` cell measured the
    brake from the negative side - does the session stay direct when it should -
    and Pilotfish's positive-controls table (read 2026-09-05) showed what the
    other side looks like: a stable, fully specified, mechanical edit across a
    dozen files with its own acceptance test, where the cheap mechanical worker
    is the right call. Nothing here is ambiguous; the only decision is who does
    it.
    """
    built = [_write(root, "adapters/__init__.py", "")]
    for index in range(1, count + 1):
        name = f"a{index:02d}"
        built.append(_write(root, f"adapters/{name}.py",
                            f'"""Transport adapter {name}."""\n\nVERSION = 1\n\n\n'
                            f'def handle(payload):\n'
                            f'    return {{"adapter": "{name}", "version": VERSION, '
                            f'"payload": payload}}\n'))
    built.append(_write(root, "tests/__init__.py", ""))
    built.append(_write(root, "tests/test_adapters.py", "\n".join([
        "import importlib",
        "import unittest",
        "",
        f'NAMES = [f"a{{index:02d}}" for index in range(1, {count + 1})]',
        "",
        "",
        "class AdapterVersions(unittest.TestCase):",
        "    def test_every_adapter_declares_version_two(self):",
        "        for name in NAMES:",
        "            with self.subTest(adapter=name):",
        '                module = importlib.import_module(f"adapters.{name}")',
        "                self.assertEqual(module.VERSION, 2)",
        '                self.assertEqual(module.handle({"k": 1})["version"], 2)',
        "",
    ])))
    built.append(_write(root, "README.md", "\n".join([
        "# Adapters",
        "",
        f"{count} transport adapters, one module each under `adapters/`. The next release",
        "bumps every adapter's `VERSION` from 1 to 2 and nothing else; `tests/` asserts",
        "the new value and stays red until all of them have moved.",
        "",
    ])))
    return built


def build_d3(root: Path) -> list[str]:
    return _build_adapters(root, 12)


def build_d4(root: Path) -> list[str]:
    """Forty-eight adapters: the same shape at four times the size, to find
    the scale at which dispatching stops costing more than doing it inline
    (d3/d3x on 2026-09-06: dispatch was two to four times inline at twelve)."""
    return _build_adapters(root, 48)


D5_KINDS = ("bump", "timeout", "rename", "retire")

D5_TODO = {
    "bump": "bump VERSION from 1 to 2",
    "timeout": ("add a module constant TIMEOUT_MS = {value} and return it "
                "under the key \"timeout_ms\""),
    "rename": "rename handle to dispatch; the body stays as it is",
    "retire": ("this adapter is retired: add DEPRECATED = True and make "
               "handle raise NotImplementedError"),
}


def d5_rows(count: int = 48) -> list[tuple[str, str, int | None]]:
    """What each adapter's TODO asks for: (name, kind, value).

    Blocks of four, each holding every kind once and shifted by one from the
    block before, so the kinds come out equal at any multiple of four and no
    two neighbours share one. The grader and the fixture's own suite both
    read this table; the builder is the only place it lives.
    """
    rows = []
    for index in range(1, count + 1):
        block, slot = divmod(index - 1, 4)
        kind = D5_KINDS[(slot + block) % 4]
        value = 500 + index * 37 if kind == "timeout" else None
        rows.append((f"a{index:02d}", kind, value))
    return rows


def _build_varied_adapters(root: Path, count: int) -> list[str]:
    """Forty-eight adapters that each need a different mechanical edit.

    d4 (2026-09-06) found same-shaped edits across forty-eight files cheapest
    in the main session's own shell - two of three inline runs did the lot
    with one loop and no Edit call - so batch size never turned the cost
    over. The shape that could is one a loop cannot do: every file says at
    its head what it needs, four kinds of change with per-file values, all
    mechanical, none the same as its neighbour. The instruction lives in the
    file rather than in a table so the work is read-then-edit per file,
    which is where a cheaper tier's per-file price would show if it exists.
    """
    built = [_write(root, "adapters/__init__.py", "")]
    for name, kind, value in d5_rows(count):
        todo = D5_TODO[kind].format(value=value)
        built.append(_write(root, f"adapters/{name}.py",
                            f'"""Transport adapter {name}."""\n'
                            f'# TODO(migration): {todo}\n\n'
                            f'VERSION = 1\n\n\n'
                            f'def handle(payload):\n'
                            f'    return {{"adapter": "{name}", "version": VERSION, '
                            f'"payload": payload}}\n'))
    expected = ",\n".join(f'    "{name}": ("{kind}", {value!r})'
                          for name, kind, value in d5_rows(count))
    built.append(_write(root, "tests/__init__.py", ""))
    built.append(_write(root, "tests/test_migration.py", "\n".join([
        "import importlib",
        "import pathlib",
        "import unittest",
        "",
        'ADAPTERS = pathlib.Path(__file__).resolve().parent.parent / "adapters"',
        "EXPECTED = {",
        expected + ",",
        "}",
        "",
        "",
        "class Migration(unittest.TestCase):",
        "    def test_no_todo_is_left(self):",
        "        for name in EXPECTED:",
        "            with self.subTest(adapter=name):",
        '                text = (ADAPTERS / f"{name}.py").read_text(encoding="utf-8")',
        '                self.assertNotIn("TODO(migration)", text)',
        "",
        "    def test_every_adapter_did_what_its_todo_said(self):",
        "        for name, (kind, value) in EXPECTED.items():",
        "            with self.subTest(adapter=name, kind=kind):",
        '                module = importlib.import_module(f"adapters.{name}")',
        '                if kind == "bump":',
        "                    self.assertEqual(module.VERSION, 2)",
        '                    self.assertEqual(module.handle({"k": 1})["version"], 2)',
        '                elif kind == "timeout":',
        "                    self.assertEqual(module.TIMEOUT_MS, value)",
        '                    self.assertEqual(module.handle({"k": 1})["timeout_ms"], value)',
        '                elif kind == "rename":',
        '                    self.assertFalse(hasattr(module, "handle"))',
        '                    self.assertEqual(module.dispatch({"k": 1})["adapter"], name)',
        '                elif kind == "retire":',
        "                    self.assertTrue(module.DEPRECATED)",
        "                    with self.assertRaises(NotImplementedError):",
        '                        module.handle({"k": 1})',
        "",
    ])))
    built.append(_write(root, "README.md", "\n".join([
        "# Transport adapters",
        "",
        f"{count} transport adapters, one module each under `adapters/`. Each file",
        "carries a `# TODO(migration): ...` line at its head saying what that one",
        "file needs for the next release. The change differs from file to file;",
        "all of them are mechanical. Do what each TODO says, remove the TODO line,",
        f"and change nothing else. `tests/` is red until all {count} are done.",
        "",
    ])))
    return built


def build_d5(root: Path) -> list[str]:
    return _build_varied_adapters(root, 48)


def build_z1(root: Path) -> list[str]:
    """One customer-facing paragraph carrying four Chinese tells and nothing else.

    The four shapes are the ones `readable-zh-tw` gained on 2026-09-05 from
    sepia's `languages/zh.md`: verb padding (進行討論, 加以說明), second person
    aimed at a reader who is not in the sentence (您可以), nominalisation
    (標準化與規範性) and 事實上 as a paragraph opener. Planted once each, so a
    rewrite either removes a shape or it does not; the last paragraph is plain,
    so a rewrite has something to leave alone.
    """
    built = [_write(root, "notes/draft.md", "\n".join([
        "# 給客戶的說明",
        "",
        "事實上，我們已經針對這次的延遲進行討論，並且會在下週的會議上加以說明。"
        "您可以在附件看到整個流程的標準化與規範性，這對於後續的合作是非常重要的。",
        "",
        "新版排程會在 9 月 15 日上線。上線前一天我們會再寄一次提醒。",
        "",
    ]))]
    built.append(_write(root, "README.md", "\n".join([
        "# 客戶溝通",
        "",
        "`notes/draft.md` 是要發給客戶的一段說明, 尚未定稿.",
        "",
    ])))
    return built


BUILDERS = {
    "r1-interrupted-resume": build_r1,
    "r2-successive-corrections": build_r2,
    "r3-conflicting-leaves": build_r3,
    "q1-clause-verdicts": build_q1,
    "q2-unstated-shape": build_q2,
    "v1-verify-before-report": build_v1,
    "v2-green-test-misses-it": build_v2,
    "v3-regression-across-turns": build_v3,
    "e1-lever-that-misses": build_e1,
    "e6-success-that-lies": build_e6,
    "e2-check-that-cannot-fail": build_e2,
    "e3-cause-you-cannot-read": build_e3,
    "e4-condition-typed-beside-the-artifact": build_e4,
    "e5-authority-both-ways": build_e5,
    "d3-twelve-adapters": build_d3,
    "d4-forty-eight-adapters": build_d4,
    "d5-forty-eight-varied-adapters": build_d5,
    "z1-zh-draft": build_z1,
}


def build(scenario: str, root: Path) -> list[str]:
    if scenario not in BUILDERS:
        raise SystemExit(f"no fixture for {scenario!r}; "
                         f"known: {', '.join(sorted(BUILDERS))}")
    root.mkdir(parents=True, exist_ok=True)
    return BUILDERS[scenario](root)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=sorted(BUILDERS))
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    for name in build(args.scenario, args.root):
        print(name)
