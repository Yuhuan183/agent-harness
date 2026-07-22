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



if __name__ == '__main__':
    unittest.main()
