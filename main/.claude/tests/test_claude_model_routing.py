"""Contract tests for the Claude-side model-routing resolver."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "main/.claude/scripts/model-routing"
AGENTS_DIR = ROOT / "main/.claude/agents"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True)


class ClaudeModelRoutingCLI(unittest.TestCase):
    def test_validates_tracked_config(self) -> None:
        self.assertTrue(os.access(SCRIPT, os.X_OK))
        result = run("validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("valid: 3 profiles", result.stdout)

    def test_resolves_deployment_preset_routes(self) -> None:
        result = run("resolve", "--role", "executor")
        self.assertEqual(result.returncode, 0, result.stderr)
        route = json.loads(result.stdout)
        self.assertEqual(route["profile"], "balanced")
        self.assertEqual(route["application"], "frontmatter_pin")
        self.assertEqual(route["model"], "claude-opus-4-8")
        self.assertEqual(route["effort"], "medium")
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
                    "model: opus", "model: haiku"
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

    def test_activate_profile_is_atomic_and_does_not_touch_source_fixture(self) -> None:
        source_config = ROOT / "main/.claude/model-routing.toml"
        source_before = source_config.read_text(encoding="utf-8")
        source_agents = {
            path.name: path.read_text(encoding="utf-8")
            for path in AGENTS_DIR.glob("*.md")
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            config = temp / "model-routing.toml"
            agents = temp / "agents"
            agents.mkdir()
            shutil.copy(source_config, config)
            for path in AGENTS_DIR.glob("*.md"):
                shutil.copy(path, agents / path.name)
            before = {
                path.name: path.read_text(encoding="utf-8")
                for path in agents.glob("*.md")
            }

            dry_run = run(
                "--config", str(config), "activate-profile", "--profile", "fast",
                "--agents-dir", str(agents), "--dry-run",
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertEqual(before, {
                path.name: path.read_text(encoding="utf-8")
                for path in agents.glob("*.md")
            })
            self.assertIn('default = "balanced"', config.read_text(encoding="utf-8"))

            activated = run(
                "--config", str(config), "activate-profile", "--profile", "fast",
                "--agents-dir", str(agents),
            )
            self.assertEqual(activated.returncode, 0, activated.stderr)
            self.assertIn("activated deployment preset: fast", activated.stdout)
            checked = run(
                "--config", str(config), "check-pins", "--profile", "fast",
                "--agents-dir", str(agents),
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertIn('default = "fast"', config.read_text(encoding="utf-8"))
            self.assertIn("model: opus", (agents / "executor.md").read_text())
            self.assertIn("effort: low", (agents / "executor.md").read_text())

        self.assertEqual(source_before, source_config.read_text(encoding="utf-8"))
        self.assertEqual(source_agents, {
            path.name: path.read_text(encoding="utf-8")
            for path in AGENTS_DIR.glob("*.md")
        })

    def test_revision_policy_is_required(self) -> None:
        original = (ROOT / "main/.claude/model-routing.toml").read_text(encoding="utf-8")
        invalid = original.replace("min_samples = 10\n", "", 1)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "model-routing.toml"
            config.write_text(invalid, encoding="utf-8")
            result = run("--config", str(config), "validate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("revision_policy keys", result.stderr)



REVISE = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-revise"


class ExperienceReviseTests(unittest.TestCase):
    def test_suggests_only_floor_compliant_routes_at_min_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = []
            # current executor route performs poorly...
            rows += [{"ts": "2026-07-20T00:00:00+00:00", "schema": 3,
                      "role": "executor", "profile": "balanced",
                      "provider": "claude", "model": "claude-opus-4-8",
                      "effort": "medium", "task_class": "impl",
                      "request_source": "claude-code", "outcome": "failed"}] * 10
            # ...opus/high (meets the judgment floor) performs well...
            rows += [{"ts": "2026-07-20T00:00:00+00:00", "schema": 3,
                      "role": "executor", "profile": "balanced",
                      "provider": "claude", "model": "claude-opus-4-8",
                      "effort": "high", "task_class": "impl",
                      "request_source": "claude-code", "outcome": "accepted"}] * 10
            # ...and sonnet/low also performs well but falls below the floor.
            rows += [{"ts": "2026-07-20T00:00:00+00:00", "schema": 3,
                      "role": "executor", "profile": "balanced",
                      "provider": "claude", "model": "claude-sonnet-5",
                      "effort": "low", "task_class": "impl",
                      "request_source": "claude-code", "outcome": "accepted"}] * 10
            ledger.write_text("\n".join(json.dumps(r) for r in rows),
                              encoding="utf-8")
            result = subprocess.run(
                [str(REVISE), "--claude-config", str(ROOT / "main/.claude/model-routing.toml"),
                 "--codex-config", str(ROOT / "main/.codex/model-routing.toml"),
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
            self.assertIn("suggestions are cohort-local", result.stdout)

    def test_rejects_mismatched_provider_revision_policies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex = Path(temp_dir) / "codex.toml"
            codex.write_text(
                (ROOT / "main/.codex/model-routing.toml").read_text(encoding="utf-8")
                .replace("prefer_probability = 0.90", "prefer_probability = 0.91"),
                encoding="utf-8",
            )
            result = subprocess.run(
                [str(REVISE),
                 "--claude-config", str(ROOT / "main/.claude/model-routing.toml"),
                 "--codex-config", str(codex)],
                capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("revision_policy values must match", result.stderr)

    def test_revision_does_not_pool_different_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = []
            for profile in ("balanced", "fast"):
                rows += [{
                    "ts": "2026-07-20T00:00:00+00:00", "schema": 3,
                    "role": "executor", "profile": profile,
                    "provider": "claude", "model": "claude-opus-4-8",
                    "effort": "medium", "task_class": "impl",
                    "request_source": "claude-code", "outcome": "failed",
                }] * 5
            rows += [{
                "ts": "2026-07-20T00:00:00+00:00", "schema": 3,
                "role": "executor", "profile": "balanced",
                "provider": "claude", "model": "claude-opus-4-8",
                "effort": "high", "task_class": "impl",
                "request_source": "claude-code", "outcome": "accepted",
            }] * 10
            ledger.write_text("\n".join(json.dumps(row) for row in rows),
                              encoding="utf-8")
            result = subprocess.run(
                [str(REVISE), "--json", "--now", "2026-07-21T00:00:00+00:00"],
                capture_output=True, text=True,
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger)},
                check=True,
            )
        report = json.loads(result.stdout)
        executor = next(
            row for row in report["rows"]
            if row["provider"] == "claude" and row["role"] == "executor"
            and row["task_class"] == "impl"
        )
        self.assertEqual(executor["profile"], "balanced")
        self.assertEqual(executor["status"], "insufficient")
        self.assertIn("current cell n=5<10", executor["detail"])


if __name__ == "__main__":
    unittest.main()
