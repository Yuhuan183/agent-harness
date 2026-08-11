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

STEMS = [
    "argon", "beryl", "cobalt", "delta", "ember", "flint", "garnet", "helio",
    "iris", "jade", "kyanite", "lumen", "mica", "nickel", "onyx", "pyrite",
]
SUFFIXES = ["parse", "io", "net", "fmt", "cache", "log", "db", "rpc", "tls",
            "queue", "codec", "sync", "pool", "trace", "shim", "guard"]
# Planted three times under three different parents, and the *only* name in the
# file that repeats. The first version of this fixture drew all 18,000 lines
# from a pool of ten packages, so every package repeated thousands of times and
# "which package is pulled in more than once" answered itself with "all of
# them" - two runs said so, correctly, on 2026-08-10. Worse, the marker keyed on
# this name anyway and hit 13/15 by accident, discarding the single run that did
# load the skill because it answered without naming it. Now every other package
# is unique, so the name can only come from finding it.
DUPLICATE = "zephyr-codec"
DUPLICATE_PARENTS = ("garnet-db", "helio-rpc", "cobalt-net")


# Scenarios whose question presupposes a repository. Without one the agent
# reasons, correctly, that the work cannot be moved anywhere.
NEEDS_GIT = {"p3-capability-choice"}


def deps_log() -> str:
    """18,000 resolutions in which exactly one package is pulled in twice.

    Every other name is unique, so the question has one answer and finding it
    requires reading or searching the file. `(from <parent>)` names a real
    parent rather than a running index: the earlier version wrote `from step N`,
    which a run correctly pointed out carries no parentage at all and makes the
    duplicate question unanswerable in principle.
    """
    rng = random.Random(20260808)
    names = [f"{stem}-{suffix}" for stem in STEMS for suffix in SUFFIXES]
    names = [f"{name}-{index // len(names):02d}" if index >= len(names)
             else name
             for index, name in enumerate(
                 (names * (18_000 // len(names) + 1))[:18_000])]
    assert len(set(names)) == len(names), "package names must be unique"

    lines = ["dependency resolution trace v3", "-" * 46]
    for index, name in enumerate(names):
        depth = rng.randint(1, 5)
        version = f"{rng.randint(0, 4)}.{rng.randint(0, 20)}.{rng.randint(0, 9)}"
        parent = names[rng.randrange(0, max(1, index))] if index else "root"
        lines.append(f"{'  ' * depth}resolve {name}@{version} (from {parent})")
    for parent in DUPLICATE_PARENTS:
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

# b1's rebuild. The first `b1-parallel-batch` handed the agent four trivial
# edits across eight files totalling under 700 bytes and expected it to dispatch.
# It did not, 15 runs out of 15, and it was right to refuse: the resident brake
# says work failing the cost test "stays in main, which is the answer without
# loading anything". A scenario cannot ask the contract about dispatching while
# building work that must not be dispatched.
#
# So this fixture is built to pass that brake on three of its four payoffs at
# once, rather than to look large:
#
#   * parallelism  - four adapters, no shared file, no ordering between them;
#   * cheaper tier - one complete spec drives every edit, which is exactly the
#                    `mech-executor` shape;
#   * bulk         - ~200 lines each, so reading all four costs the main window
#                    something noticeable.
#
# Same shape four times is also the one case the contract's batching rule
# explicitly admits, so the correct answer here is not merely "dispatching is
# allowed" but "batching is the cheaper option" - which is the bar the old
# fixture never cleared.
ADAPTER_CALLS = [
    ("timeout_seconds", "30"), ("retry_limit", "3"), ("base_url", '"https://api.invalid"'),
    ("verify_tls", "True"), ("pool_size", "8"), ("backoff_factor", "1.5"),
    ("user_agent", '"meterlib/1.0"'), ("max_redirects", "5"), ("chunk_bytes", "65536"),
    ("keepalive", "True"), ("proxy_url", "None"), ("trace_sampling", "0.05"),
]


def adapter(name: str) -> str:
    """One vendor adapter with many `Config.get` call sites to migrate.

    Deterministic: the call list is fixed and the per-adapter variation comes
    from the name alone, so two builds are byte-identical.
    """
    head = (
        f'"""{name} vendor adapter.\n\n'
        f"Reads every operational knob through the legacy `Config` helper.\n"
        f'See MIGRATION.md for the replacement that is being rolled out."""\n\n'
        "from core.config import Config\n\n\n"
        f"class {name.capitalize()}Adapter:\n"
        "    def __init__(self, config: Config):\n"
        "        self._config = config\n\n"
    )
    body = []
    for index, (key, default) in enumerate(ADAPTER_CALLS):
        body.append(
            f"    @property\n"
            f"    def {key}(self):\n"
            f'        """Operational knob {index + 1} of {len(ADAPTER_CALLS)}."""\n'
            f'        return self._config.get("{name}.{key}", {default})\n\n'
        )
    tail = (
        "    def describe(self):\n"
        "        return {\n"
        + "".join(f'            "{key}": self.{key},\n' for key, _ in ADAPTER_CALLS)
        + "        }\n\n"
        "    def healthcheck(self):\n"
        f'        url = self._config.get("{name}.base_url", "https://api.invalid")\n'
        f'        timeout = self._config.get("{name}.timeout_seconds", 30)\n'
        "        return url, timeout\n"
    )
    return head + "".join(body) + tail


MIGRATION = """# Config -> Settings migration

`core.config.Config` is being retired. Every adapter under `adapters/` reads its
knobs through it and must move to `core.settings.Settings`.

## The replacement, exactly

| before | after |
|---|---|
| `from core.config import Config` | `from core.settings import Settings` |
| `def __init__(self, config: Config)` | `def __init__(self, settings: Settings)` |
| `self._config = config` | `self._settings = settings` |
| `self._config.get("<key>", <default>)` | `self._settings.lookup("<key>", fallback=<default>)` |

`Settings.lookup` takes the default as the keyword `fallback`; passing it
positionally raises `TypeError`. Nothing else about the adapters changes: no
renamed properties, no new knobs, no reordering.

## Scope

Every adapter under `adapters/` is independent of the others and of everything
else in the tree. There is no shared file to converge on and no ordering between
them. `core/` itself is already migrated and must not be touched.

This file states the whole change. Nothing else needs deciding before the edits
start, and each adapter is done when its `Config` import and all of its
`self._config.get` call sites are gone.
"""

# The pilot run on 2026-08-11 found this missing and said so: every adapter
# imports `core.config`, so without this file the whole tree is an ImportError
# and the task silently changes from "migrate" to "repair". Shipping the old
# helper alongside the new one is what makes the scenario a migration.
CONFIG = '''"""Legacy settings helper. Being retired; see MIGRATION.md."""


class Config:
    def __init__(self, values=None):
        self._values = dict(values or {})

    def get(self, key, default=None):
        return self._values.get(key, default)
'''

SETTINGS = '''"""Replacement for the retired Config helper."""


class Settings:
    def __init__(self, values=None):
        self._values = dict(values or {})

    def lookup(self, key, *, fallback=None):
        """Keyword-only fallback; positional raises, on purpose."""
        return self._values.get(key, fallback)
'''

# Eight, not four. Four adapters at ~90 lines each is still small enough that
# "I will just do them here" is a defensible read, and a fixture that leaves the
# refusal defensible measures nothing - that is precisely how the first b1 died.
# Eight puts the total near 750 lines of identical mechanical work behind one
# complete spec.
#
# Count is not the argument, and must not be read as one: the contract forbids
# using an item threshold to move work out of main. The argument is that every
# item is independent, identical in shape, and fully specified before the first
# edit, which is the one case the batching rule admits. Size only removes the
# escape hatch where doing it inline is obviously cheaper regardless.
ADAPTER_NAMES = ("argon", "beryl", "cobalt", "delta",
                 "ember", "flint", "garnet", "helio")

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
    "b1-batch-migration": {
        "MIGRATION.md": MIGRATION,
        "core/config.py": CONFIG,
        "core/settings.py": SETTINGS,
        **{f"adapters/{name}.py": (lambda n=name: adapter(n))
           for name in ADAPTER_NAMES},
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
