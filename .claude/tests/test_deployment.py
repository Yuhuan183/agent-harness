"""Deployment boundary: machine-state hygiene and manifest-driven sync."""
from support import *  # noqa: F401,F403


class MachineStateHygieneTests(unittest.TestCase):
    PORTABLE_TEXT_FILES = (
        ".claude/CLAUDE.contract.md",
        ".claude/README.md",
        ".claude/settings.json",
        ".claude/examples/headroom-mcp.merge.json",
        ".claude/skills/baton-dispatch/SKILL.md",
        ".claude/skills/provider-routing/SKILL.md",
        ".codex/AGENTS.contract.md",
        ".codex/ANALYSIS.md",
        ".codex/DEPLOY.md",
        ".codex/config.merge.toml",
        ".codex/README.md",
        "docs/setup.md",
        "README.md",
        "scripts/sync.sh",
    )

    def test_no_absolute_home_paths_leak_into_tracked_config(self) -> None:
        for path in self.PORTABLE_TEXT_FILES:
            self.assertNotIn("/Users/", read(path), path)

    def test_machine_state_files_are_gitignored(self) -> None:
        ignore = read(".gitignore")
        for entry in (".claude/mcp_servers.json", ".codex/config.toml", "__pycache__/", "*.pyc"):
            self.assertIn(entry, ignore)
        # Confirmed ignored by git itself (exit 0 == path is ignored).
        for path in (".claude/mcp_servers.json", ".codex/config.toml"):
            self.assertEqual(git("check-ignore", path).returncode, 0, path)
        # And not tracked.
        tracked = git("ls-files").stdout.splitlines()
        self.assertNotIn(".claude/mcp_servers.json", tracked)
        self.assertNotIn(".codex/config.toml", tracked)

    def test_settings_are_user_owned_and_portable(self) -> None:
        settings = json.loads(read(".claude/settings.json"))
        for key in ("model", "effortLevel", "fallbackModel"):
            self.assertNotIn(key, settings)
        self.assertNotIn("ANTHROPIC_BASE_URL", settings.get("env", {}))
        mcp_text = read(".claude/examples/headroom-mcp.merge.json")
        self.assertNotIn("/Users/", mcp_text)
        self.assertEqual(
            json.loads(mcp_text)["mcpServers"]["headroom"],
            {"command": "headroom", "args": ["mcp", "serve"]},
        )

    def test_one_rtk_hook_and_one_runtime_guard(self) -> None:
        settings = json.loads(read(".claude/settings.json"))
        pre = [h["command"] for g in settings["hooks"]["PreToolUse"] for h in g["hooks"]]
        start = [h["command"] for g in settings["hooks"]["SessionStart"] for h in g["hooks"]]
        self.assertEqual(sum("rtk hook claude" in c for c in pre), 1)
        self.assertEqual(sum("runtime-guard.py\" --gate" in c for c in pre), 1)
        self.assertEqual(sum("runtime-guard.py" in c for c in start), 1)
        self.assertEqual(sum("commit-test-gate.py" in c for c in pre), 1)

    def test_commit_gate_blocks_red_suites_and_skips_foreign_repos(self) -> None:
        # Behavioral proof with a planted failure — a gate that cannot catch a
        # deliberate error does not exist. Uses a synthetic repo so the check
        # never recurses into this suite.
        hook = ROOT / ".claude/hooks/commit-test-gate.py"

        def run_hook(command: str, cwd: str) -> subprocess.CompletedProcess[str]:
            payload = json.dumps({"tool_input": {"command": command}, "cwd": cwd})
            return subprocess.run(
                [sys.executable, str(hook)], input=payload,
                capture_output=True, text=True, timeout=120,
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            # no .claude/tests -> pass through
            self.assertEqual(run_hook("git commit -m x", str(repo)).returncode, 0)
            tests = repo / ".claude" / "tests"
            tests.mkdir(parents=True)
            (tests / "test_red.py").write_text(
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_red(self):\n"
                "        self.fail('planted')\n",
                encoding="utf-8",
            )
            blocked = run_hook("git commit -m x", str(repo))
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("commit blocked", blocked.stderr)
            self.assertEqual(
                run_hook("AGENT_SKIP_TEST_GATE=1 git commit -m x", str(repo)).returncode, 0
            )
            # The escape hatch is a leading shell assignment only — the token
            # inside a commit message (or anywhere else) must not disarm the
            # gate (review F-01).
            msg_form = run_hook(
                "git commit -m 'document AGENT_SKIP_TEST_GATE=1 behavior'", str(repo)
            )
            self.assertEqual(msg_form.returncode, 2)
            self.assertIn("commit blocked", msg_form.stderr)
            self.assertEqual(run_hook("git status", str(repo)).returncode, 0)
            # Repo-switching forms must gate on the command's target, not cwd
            # (F-01: `git -C` and `cd &&` both bypassed the gate from cwd=/).
            dash_c = run_hook(f"git -C {repo} commit -m x", "/")
            self.assertEqual(dash_c.returncode, 2)
            self.assertIn("commit blocked", dash_c.stderr)
            cd_form = run_hook(f"cd {repo} && git commit -m x", "/")
            self.assertEqual(cd_form.returncode, 2)
            self.assertIn("commit blocked", cd_form.stderr)



if __name__ == '__main__':
    unittest.main()
