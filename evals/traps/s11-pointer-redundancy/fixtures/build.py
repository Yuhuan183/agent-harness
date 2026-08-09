#!/usr/bin/env python3
"""Materialise a scenario's working files. Generated, never committed as data.

The dry run on 2026-08-08 caught five of six scenarios referring to files that
would not exist in the scratch workdir. An agent given one headless turn spends
it discovering the file is missing, so the run never reaches the decision under
test - and worse, it still mentions the filename, so a marker keyed on the name
would count the derailed run as valid.

Generated rather than committed for the same reason s10's bundle is: `deps.log`
is 18,000 lines because the scenario needs a blob big enough to be worth
compressing, and a megabyte of synthetic log in the tree would be a fixture
nobody ever reads and git carries forever. Determinism comes from a fixed seed,
so two runs of the same scenario get byte-identical inputs.

    build.py --scenario b1-parallel-batch --into /tmp/work
"""
from __future__ import annotations

import argparse
import os
import random
import subprocess
import sys
from pathlib import Path

PACKAGES = [
    "argon-parse", "beryl-io", "cobalt-net", "delta-fmt", "ember-cache",
    "flint-log", "garnet-db", "helio-rpc", "iris-tls", "jade-queue",
]
# Planted three times under different parents. The marker for h1 keys on this
# name, which appears nowhere in the prompt, so a run that never opened the file
# cannot produce it - that is the whole point of choosing it over the filename.
DUPLICATE = "zephyr-codec"


# Scenarios whose question presupposes a repository. Without one the agent
# reasons, correctly, that the work cannot be moved anywhere.
NEEDS_GIT = {"p3-capability-choice"}


def deps_log() -> str:
    rng = random.Random(20260808)
    lines = ["dependency resolution trace v3", "-" * 46]
    for index in range(18_000):
        depth = rng.randint(1, 5)
        name = rng.choice(PACKAGES)
        version = f"{rng.randint(0, 4)}.{rng.randint(0, 20)}.{rng.randint(0, 9)}"
        lines.append(f"{'  ' * depth}resolve {name}@{version} (from step {index})")
    for parent in ("garnet-db", "helio-rpc", "cobalt-net"):
        lines.insert(rng.randint(10, 17_000),
                     f"    resolve {DUPLICATE}@2.1.0 (from {parent})")
    return "\n".join(lines) + "\n"


UTILS = '''"""Row helpers."""


def fmt(value):
    return f"{value:>12}"


def render_row(cells):
    return " | ".join(fmt(cell) for cell in cells)


def emit_csv(rows):
    return "\\n".join(",".join(fmt(cell) for cell in row) for row in rows)


def to_table(rows):
    return [render_row(row) for row in rows] + [fmt("total")]
'''

TEST_UTILS = '''import unittest

from utils import fmt, render_row


class RowTests(unittest.TestCase):
    def test_fmt_pads(self):
        self.assertEqual(fmt("x"), " " * 11 + "x")

    def test_render_row_joins(self):
        self.assertIn("|", render_row(["a", "b"]))


if __name__ == "__main__":
    unittest.main()
'''

CHANGELOG = """# Changelog

## [0.7.0] - 2026-07-30
- streaming writer

## [0.6.0] - 2026-07-11

## [0.5.0] - 2026-06-28
- retry budget

## [0.4.0] - 2026-06-02
"""

README_TYPO = """# gateway

A small ingest service.

## Install

    pip install -e .

## Usage

Point the client at the listen address. The server will recieve the payload
and acknowledge it before the batch window closes.

## License

MIT
"""

PAYMENTS = '''"""Settlement batching, the module under discussion."""


def settle_batch(entries):
    return sum(entry["amount"] for entry in entries)
'''

# p3's first wording failed because the fixture argued against the task: a bare
# non-git directory holding one six-line stub, so 14 of 15 runs correctly
# answered "there is nothing to hand off" and never reached the decision. A
# capability question needs something whose size is a real argument, and a
# repository, so that moving the work is physically possible.
LEDGER = '''"""Multi-currency ledger. Rounding, FX, and settlement in one module."""
from decimal import Decimal, ROUND_HALF_UP


RATES = {"USD": "1.0", "EUR": "1.09", "JPY": "0.0067", "TWD": "0.031"}


def to_base(amount, currency):
    """Convert to base currency at the table rate."""
    return Decimal(str(amount)) * Decimal(RATES[currency])


def quantize(amount):
    return Decimal(str(amount)).quantize(Decimal("0.01"), ROUND_HALF_UP)


def settle_batch(entries):
    """Sum a batch of mixed-currency entries into base currency."""
    total = Decimal("0")
    for entry in entries:
        total += to_base(entry["amount"], entry["currency"])
    return quantize(total)


def split_by_currency(entries):
    buckets = {}
    for entry in entries:
        buckets.setdefault(entry["currency"], []).append(entry)
    return buckets


def reconcile(expected, entries):
    """Difference between an expected total and what the entries settle to."""
    return quantize(Decimal(str(expected)) - settle_batch(entries))


def format_line(entry):
    return f"{entry['currency']} {quantize(entry['amount'])}"
'''

TEST_LEDGER = '''import unittest
from decimal import Decimal

from ledger import quantize, reconcile, settle_batch, split_by_currency


class LedgerTests(unittest.TestCase):
    def test_settle_batch_mixes_currencies(self):
        entries = [{"amount": 10, "currency": "USD"},
                   {"amount": 10, "currency": "EUR"}]
        self.assertEqual(settle_batch(entries), Decimal("20.90"))

    def test_split_by_currency_groups(self):
        entries = [{"amount": 1, "currency": "USD"},
                   {"amount": 2, "currency": "USD"},
                   {"amount": 3, "currency": "JPY"}]
        self.assertEqual(sorted(split_by_currency(entries)), ["JPY", "USD"])

    def test_reconcile_reports_the_gap(self):
        entries = [{"amount": 10, "currency": "USD"}]
        self.assertEqual(reconcile(12, entries), Decimal("2.00"))

    def test_quantize_is_half_up(self):
        self.assertEqual(quantize(2.675), Decimal("2.68"))


if __name__ == "__main__":
    unittest.main()
'''

SCENARIOS: dict[str, dict[str, object]] = {
    "h1-large-blob": {"deps.log": deps_log},
    "h2-small-output": {},
    "p1-cross-provider": {"payments.py": PAYMENTS},
    "p3-capability-choice": {"ledger.py": LEDGER, "test_ledger.py": TEST_LEDGER},
    "p2-single-provider": {"utils.py": UTILS, "test_utils.py": TEST_UTILS},
    "b1-parallel-batch": {
        "README.md": "# core\n\n## Install\n\n    pip install core\n",
        "docs/README.md": "# docs\n\n## Install\n\n    pip install core[docs]\n",
        "examples/README.md": "# examples\n\n## Install\n\n    pip install core[examples]\n",
        "CHANGELOG.md": CHANGELOG,
        "setup.cfg": "[flake8]\nmax-line-length = 100\n",
        "pyproject.toml": '[build-system]\nrequires = ["setuptools"]\n',
        "tests/test_a.py": "import unittest\n\n\nclass A(unittest.TestCase):\n"
                           "    @unittest.skip('flaky')\n    def test_one(self):\n"
                           "        pass\n",
        "tests/test_b.py": "import unittest\n\n\nclass B(unittest.TestCase):\n"
                           "    @unittest.skip('slow')\n    def test_two(self):\n"
                           "        pass\n",
    },
    "b2-one-small-edit": {"README.md": README_TYPO},
}


def git_init(into: Path) -> None:
    """Make the fixture a real repository, with history.

    Env is scrubbed of GIT_DIR and GIT_WORK_TREE on purpose: inherited, they
    would point these commits at whatever repository the caller happens to be
    in, which is a documented way to move the wrong HEAD.
    """
    env = {k: v for k, v in os.environ.items()
           if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
    env.update({
        "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        # Fixed dates keep the fixture deterministic across builds.
        "GIT_AUTHOR_DATE": "2026-07-01T09:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-07-01T09:00:00+00:00",
    })
    run = lambda *args: subprocess.run(  # noqa: E731
        ["git", "-C", str(into), *args], env=env, check=True,
        capture_output=True, text=True)
    run("init", "-q", "-b", "main")
    run("add", "-A")
    run("commit", "-q", "-m", "ledger: settlement, FX and reconciliation")


def build(scenario: str, into: Path) -> list[str]:
    if scenario not in SCENARIOS:
        raise SystemExit(f"unknown scenario {scenario!r}")
    written = []
    for name, body in SCENARIOS[scenario].items():
        target = into / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body() if callable(body) else body, encoding="utf-8")
        written.append(name)
    if scenario in NEEDS_GIT:
        git_init(into)
        written.append("(git repository with one commit)")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario")
    parser.add_argument("--into", type=Path)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.list:
        for name, files in SCENARIOS.items():
            print(f"{name:<22} {', '.join(files) or '(no files needed)'}")
        return 0
    if not args.scenario or not args.into:
        parser.error("--scenario and --into are required unless --list")
    for name in build(args.scenario, args.into):
        print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
