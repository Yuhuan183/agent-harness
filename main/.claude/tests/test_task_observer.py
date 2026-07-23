"""Task-observer opt-in contract and append-only ledger."""

from __future__ import annotations

import concurrent.futures
import uuid

from support import *  # noqa: F401,F403


SCRIPT = ROOT / "main/.agents/skills/task-observer/scripts/observation-log"


def run_observer(
    ledger: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        env={**os.environ, "AGENT_SKILL_OBSERVATIONS": str(ledger)},
        capture_output=True,
        text=True,
        timeout=20,
    )


def add_args(index: int = 1) -> tuple[str, ...]:
    return (
        "add",
        "--skill", "example-skill",
        "--area", "verification",
        "--issue", f"check {index} relied on a prose promise",
        "--improvement", "add a deterministic acceptance check",
        "--principle", "mechanise fragile acceptance claims",
        "--type", "open-source",
    )


class TaskObserverTests(unittest.TestCase):
    def test_shared_layout_manifest_and_opt_in_policy(self) -> None:
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(os.access(SCRIPT, os.X_OK))
        for stub in (
            ROOT / "main/.claude/skills/task-observer",
            ROOT / "main/.codex/skills/task-observer",
        ):
            self.assertTrue(stub.is_symlink(), stub)
            self.assertEqual(
                os.readlink(stub), "../../.agents/skills/task-observer"
            )
            self.assertTrue((stub / "SKILL.md").is_file())
        for pair in (
            ("main/.agents/skills/task-observer", ".agents/skills/task-observer"),
            ("main/.claude/skills/task-observer", ".claude/skills/task-observer"),
            ("main/.codex/skills/task-observer", ".codex/skills/task-observer"),
        ):
            self.assertIn(pair, deployment_manifest())
        skill = read(".agents/skills/task-observer/SKILL.md")
        self.assertIn("Do not invoke for ordinary task execution", skill)
        self.assertIn("Never activate merely because", skill)
        self.assertIn("不滿意", skill)
        self.assertIn("not what I asked", skill)
        self.assertIn("ask once", skill)
        self.assertIn("Handle the requested correction or rework first", skill)
        self.assertIn("If the user declines or ignores", skill)
        self.assertIn("Never edit, install, deploy, commit, publish, or delete", skill)
        openai = read(".agents/skills/task-observer/agents/openai.yaml")
        self.assertIn("allow_implicit_invocation: true", openai)
        sync = read("scripts/sync.sh")
        self.assertIn('"$HOME/.claude/skills/task-observer"', sync)
        self.assertIn('"$HOME/.codex/skills/task-observer"', sync)
        attribution = read(".agents/skills/task-observer/ATTRIBUTION.md")
        self.assertIn("Eoghan Henn", attribution)
        self.assertIn("Creative Commons Attribution 4.0", attribution)
        self.assertIn("v2.0.0", attribution)
        self.assertIn(
            "281f13466cd3a73e9ebc9d210907748e1941a3dd", attribution
        )

    def test_missing_ledger_review_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "nested" / "observations.jsonl"
            reviewed = run_observer(ledger, "review")
            self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
            self.assertIn("Open observations: 0", reviewed.stdout)
            self.assertFalse(ledger.exists())
            self.assertFalse(ledger.parent.exists())

    def test_add_list_review_and_resolve_are_event_sourced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "observations.jsonl"
            added = run_observer(ledger, *add_args())
            self.assertEqual(added.returncode, 0, added.stderr)
            observation_id = added.stdout.strip()
            uuid.UUID(observation_id)

            listed = run_observer(ledger, "list", "--status", "open", "--json")
            self.assertEqual(listed.returncode, 0, listed.stderr)
            records = json.loads(listed.stdout)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["id"], observation_id)
            self.assertEqual(records[0]["status"], "open")

            reviewed = run_observer(ledger, "review")
            self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
            self.assertIn(observation_id, reviewed.stdout)
            self.assertIn("## example-skill", reviewed.stdout)

            resolved = run_observer(
                ledger, "resolve", "--id", observation_id,
                "--resolution", "actioned",
                "--note", "added and verified the deterministic check",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            events = [json.loads(line) for line in ledger.read_text().splitlines()]
            self.assertEqual(
                [event["event"] for event in events],
                ["observation_created", "observation_resolved"],
            )

            actioned = run_observer(
                ledger, "list", "--status", "actioned", "--json"
            )
            records = json.loads(actioned.stdout)
            self.assertEqual(records[0]["status"], "actioned")
            self.assertEqual(
                records[0]["resolution_note"],
                "added and verified the deterministic check",
            )
            duplicate = run_observer(
                ledger, "resolve", "--id", observation_id,
                "--resolution", "declined", "--note", "duplicate",
            )
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn("already resolved", duplicate.stderr)
            self.assertEqual(len(ledger.read_text().splitlines()), 2)

    def test_parallel_appends_are_valid_and_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "observations.jsonl"

            def add(index: int) -> subprocess.CompletedProcess[str]:
                return run_observer(ledger, *add_args(index))

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(add, range(24)))

            for result in results:
                self.assertEqual(result.returncode, 0, result.stderr)
            events = [json.loads(line) for line in ledger.read_text().splitlines()]
            self.assertEqual(len(events), 24)
            self.assertEqual(len({event["id"] for event in events}), 24)
            self.assertTrue(all(event["schema_version"] == 1 for event in events))
            listed = run_observer(ledger, "list", "--status", "open", "--json")
            self.assertEqual(len(json.loads(listed.stdout)), 24)

    def test_invalid_or_unknown_transitions_fail_without_appending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "nested" / "observations.jsonl"
            empty = run_observer(
                ledger, "add", "--skill", "x", "--area", "x",
                "--issue", " ", "--improvement", "x", "--principle", "x",
            )
            self.assertEqual(empty.returncode, 2)
            self.assertFalse(ledger.exists())
            self.assertFalse(ledger.parent.exists())
            unknown = run_observer(
                ledger, "resolve", "--id", str(uuid.uuid4()),
                "--resolution", "declined", "--note", "not applicable",
            )
            self.assertEqual(unknown.returncode, 2)
            self.assertFalse(ledger.exists())

    def test_malformed_events_are_rejected_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "observations.jsonl"
            malformed_created = {
                "schema_version": 1,
                "event": "observation_created",
                "id": str(uuid.uuid4()),
                "recorded_at": "2026-07-23T00:00:00+00:00",
            }
            ledger.write_text(json.dumps(malformed_created) + "\n", encoding="utf-8")
            reviewed = run_observer(ledger, "review")
            self.assertEqual(reviewed.returncode, 2)
            self.assertIn("skill must be a non-empty string", reviewed.stderr)
            self.assertNotIn("Traceback", reviewed.stderr)

            ledger.write_text("[]\n", encoding="utf-8")
            non_object = run_observer(ledger, "list", "--json")
            self.assertEqual(non_object.returncode, 2)
            self.assertIn("must be a JSON object", non_object.stderr)
            self.assertNotIn("Traceback", non_object.stderr)

            added = run_observer(ledger, *add_args())
            self.assertEqual(added.returncode, 2)
            self.assertIn("must be a JSON object", added.stderr)
            self.assertEqual(ledger.read_text(encoding="utf-8"), "[]\n")


if __name__ == "__main__":
    unittest.main()
