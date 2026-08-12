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


BUILDERS = {
    "r1-interrupted-resume": build_r1,
    "r2-successive-corrections": build_r2,
    "r3-conflicting-leaves": build_r3,
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
