"""Contract tests for the Claude-side model-routing resolver."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".claude/scripts/model-routing"
AGENTS_DIR = ROOT / ".claude/agents"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True)


class ClaudeModelRoutingCLI(unittest.TestCase):
    def test_validates_tracked_config(self) -> None:
        self.assertTrue(os.access(SCRIPT, os.X_OK))
        result = run("validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("valid: 3 profiles", result.stdout)

    def test_resolves_pinned_and_follow_tier_routes(self) -> None:
        result = run("resolve", "--role", "executor")
        self.assertEqual(result.returncode, 0, result.stderr)
        route = json.loads(result.stdout)
        self.assertEqual(route["profile"], "balanced")
        self.assertEqual(route["application"], "frontmatter_pin")
        self.assertEqual(route["model"], "claude-sonnet-5")
        self.assertEqual(route["effort"], "high")
        self.assertEqual(route["invocation"]["effort_delivery"], "frontmatter_pin")

        verifier = json.loads(run("resolve", "--role", "verifier").stdout)
        self.assertEqual(verifier["model"], "claude-opus-4-8")
        self.assertEqual(verifier["effort"], "high")
        self.assertEqual(verifier["invocation"]["effort_delivery"], "frontmatter_pin")
        fast_verifier = json.loads(
            run("resolve", "--role", "verifier", "--priority", "fast").stdout
        )
        self.assertEqual(fast_verifier["effort"], "medium")

        main = json.loads(run("resolve", "--role", "main").stdout)
        self.assertEqual(main["model"], "user_selected")
        self.assertEqual(main["invocation"], {"model_delivery": "session_selector"})

    def test_check_pins_matches_tracked_agents(self) -> None:
        result = run("check-pins", "--agents-dir", str(AGENTS_DIR))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("7 roles checked", result.stdout)

    def test_check_pins_detects_model_and_effort_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            drifted = Path(temp_dir)
            for path in AGENTS_DIR.glob("*.md"):
                shutil.copy(path, drifted / path.name)
            executor = drifted / "executor.md"
            executor.write_text(
                executor.read_text(encoding="utf-8").replace(
                    "model: sonnet", "model: haiku"
                ),
                encoding="utf-8",
            )
            verifier = drifted / "verifier.md"
            verifier.write_text(
                verifier.read_text(encoding="utf-8").replace(
                    "effort: high", "effort: low"
                ),
                encoding="utf-8",
            )
            result = run("check-pins", "--agents-dir", str(drifted))
            self.assertEqual(result.returncode, 1)
            self.assertIn("executor: frontmatter pins claude-haiku-4-5", result.stderr)
            self.assertIn("verifier: frontmatter effort 'low'", result.stderr)



REVISE = ROOT / ".agents/skills/experience-ledger/scripts/experience-revise"


class ExperienceReviseTests(unittest.TestCase):
    def test_suggests_only_floor_compliant_routes_at_min_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = []
            # current executor route performs poorly...
            rows += [{"ts": "2026-07-20T00:00:00+00:00", "role": "executor",
                      "provider": "claude", "model": "claude-sonnet-5",
                      "effort": "high", "outcome": "failed"}] * 5
            # ...opus/high (meets the judgment floor) performs well...
            rows += [{"ts": "2026-07-20T00:00:00+00:00", "role": "executor",
                      "provider": "claude", "model": "claude-opus-4-8",
                      "effort": "high", "outcome": "accepted"}] * 6
            # ...and sonnet/low also performs well but falls below the floor.
            rows += [{"ts": "2026-07-20T00:00:00+00:00", "role": "executor",
                      "provider": "claude", "model": "claude-sonnet-5",
                      "effort": "low", "outcome": "accepted"}] * 6
            ledger.write_text("\n".join(json.dumps(r) for r in rows),
                              encoding="utf-8")
            result = subprocess.run(
                [str(REVISE), "--claude-config", str(ROOT / ".claude/model-routing.toml"),
                 "--codex-config", str(Path(temp_dir) / "missing.toml"),
                 "--now", "2026-07-21T00:00:00+00:00"],
                capture_output=True, text=True,
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            executor_line = next(l for l in result.stdout.splitlines()
                                 if l.startswith("claude executor"))
            self.assertIn("consider", executor_line)
            self.assertIn("claude-opus-4-8/high", executor_line)
            self.assertNotIn("claude-sonnet-5/low", executor_line)
            self.assertIn("never edits routing files", result.stdout)


if __name__ == "__main__":
    unittest.main()
