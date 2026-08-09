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
import random
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

SCENARIOS: dict[str, dict[str, object]] = {
    "h1-large-blob": {"deps.log": deps_log},
    "h2-small-output": {},
    "p1-cross-provider": {"payments.py": PAYMENTS},
    # Same fixture as p1 deliberately. p3 changes one thing only - how the
    # request is worded - so the code under discussion must stay identical or
    # the cell would vary two things at once.
    "p3-oblique-handoff": {"payments.py": PAYMENTS},
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


def build(scenario: str, into: Path) -> list[str]:
    if scenario not in SCENARIOS:
        raise SystemExit(f"unknown scenario {scenario!r}")
    written = []
    for name, body in SCENARIOS[scenario].items():
        target = into / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body() if callable(body) else body, encoding="utf-8")
        written.append(name)
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
