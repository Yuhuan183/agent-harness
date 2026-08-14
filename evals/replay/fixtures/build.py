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


BUILDERS = {
    "r1-interrupted-resume": build_r1,
    "r2-successive-corrections": build_r2,
    "r3-conflicting-leaves": build_r3,
    "q1-clause-verdicts": build_q1,
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
