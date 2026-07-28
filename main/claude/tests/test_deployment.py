"""Deployment boundary: machine-state hygiene and manifest-driven sync."""
from support import *  # noqa: F401,F403


class MachineStateHygieneTests(unittest.TestCase):
    def test_no_absolute_home_paths_leak_into_tracked_config(self) -> None:
        sources = set()
        for source_rel, _, _ in deployment_manifest_entries():
            source = ROOT / source_rel
            if source.is_dir():
                for current, dirs, files in os.walk(source, followlinks=True):
                    dirs[:] = [name for name in dirs if name != "__pycache__"]
                    for name in files:
                        if name.endswith(".pyc") or name == ".DS_Store":
                            continue
                        sources.add((Path(current) / name).resolve())
            else:
                sources.add(source.resolve())
        self.assertTrue(sources)
        for path in sorted(sources):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            self.assertNotIn("/Users/", text, str(path.relative_to(ROOT)))

    def test_machine_state_files_are_gitignored(self) -> None:
        ignore = read(".gitignore")
        for entry in ("main/claude/mcp_servers.json", "main/codex/config.toml",
                      ".claude/.headroom_wrap_marker.json", "__pycache__/", "*.pyc"):
            self.assertIn(entry, ignore)
        # Confirmed ignored by git itself (exit 0 == path is ignored).
        for path in ("main/claude/mcp_servers.json", "main/codex/config.toml"):
            self.assertEqual(git("check-ignore", path).returncode, 0, path)
        self.assertEqual(
            git("check-ignore", ".claude/.headroom_wrap_marker.json").returncode, 0
        )
        # Root-level agent directories are reserved for project-specific
        # configuration and must not inherit the deployable bundle ignores.
        for path in (".claude/mcp_servers.json", ".codex/config.toml"):
            self.assertEqual(git("check-ignore", path).returncode, 1, path)
        # And not tracked.
        tracked = git("ls-files").stdout.splitlines()
        self.assertNotIn("main/claude/mcp_servers.json", tracked)
        self.assertNotIn("main/codex/config.toml", tracked)

    def test_settings_are_user_owned_and_portable(self) -> None:
        settings = json.loads(read(".claude/settings.json"))
        for key in ("model", "effortLevel", "fallbackModel"):
            self.assertNotIn(key, settings)
        self.assertNotIn("ANTHROPIC_BASE_URL", settings.get("env", {}))
        mcp_text = read(".claude/examples/headroom-mcp.legacy.json")
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

    def test_weekly_integrity_outer_timeout_exceeds_its_inner_work(self) -> None:
        # F-06: the SessionStart hook budget must outlast its slowest internal
        # subprocess. When the outer timeout was 15s and one rsync alone was
        # 30s, a drift-heavy run got killed before writing its throttle stamp
        # and silently retried every session, never completing.
        settings = json.loads(read(".claude/settings.json"))
        outer = next(
            h["timeout"]
            for g in settings["hooks"]["SessionStart"] for h in g["hooks"]
            if "weekly-integrity.py" in h["command"]
        )
        inner = [int(m) for m in re.findall(
            r"timeout=(\d+)", read(".claude/hooks/weekly-integrity.py"))]
        self.assertGreater(outer, max(inner),
                           "weekly-integrity outer timeout must exceed its "
                           "slowest internal subprocess timeout")

    def test_headroom_routing_ownership_is_explicit(self) -> None:
        runtime = read(".agents/docs/headroom-runtime.md")
        codex = read(".codex/AGENTS.contract.md")
        setup = read("docs/setup.md")
        for text in (runtime, setup):
            self.assertIn("wrap-first", text)
            self.assertIn("`ANTHROPIC_BASE_URL`", text)
            self.assertIn("`OPENAI_BASE_URL`", text)
            self.assertIn("Codex App", text)
        self.assertIn("This contract owns RTK guidance", codex)
        self.assertIn("headroom wrap claude --no-context-tool", runtime)
        self.assertIn("headroom wrap codex --no-context-tool", runtime)
        self.assertIn("headroom wrap agy", runtime)
        self.assertIn("exit 127", runtime)
        self.assertIn("只證明當下 shell environment", runtime)
        self.assertIn("不代表本 repo 的預設", runtime)
        self.assertIn("Remote Control", runtime)
        self.assertIn("headroom learn", runtime)
        self.assertNotIn("Codex 固定依賴", runtime)
        self.assertNotIn("Codex 使用 `default` profile", runtime)
        for function_name in (
            "agy-auto",
            "hclaude",
            "hcodex",
            "hagy",
            "claude-auto",
            "codex-auto",
            "hclaude-auto",
            "hcodex-auto",
            "hagy-auto",
        ):
            self.assertIn(function_name, setup)
        self.assertIn("--permission-mode auto", runtime)
        self.assertIn("-a on-request -s workspace-write", runtime)
        self.assertIn("--mode accept-edits", runtime)

    def test_commit_gate_blocks_red_suites_and_skips_foreign_repos(self) -> None:
        # Behavioral proof with a planted failure — a gate that cannot catch a
        # deliberate error does not exist. Uses a synthetic repo so the check
        # never recurses into this suite.
        hook = ROOT / "main/claude/hooks/commit-test-gate.py"

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

            # A backslash-newline continuation is one command; the raw newline
            # must not split `git` from `commit` and slip the gate (F-02).
            cont_form = run_hook("git \\\n  commit -m x", str(repo))
            self.assertEqual(cont_form.returncode, 2)
            self.assertIn("commit blocked", cont_form.stderr)

            # The harness keeps its deployable suite under main/claude/tests.
            # A stale root cache must neither trigger a zero-test false block
            # nor hide the canonical suite.
            (tests / "test_red.py").unlink()
            (tests / "__pycache__").mkdir(exist_ok=True)
            canonical = repo / "main" / "claude" / "tests"
            canonical.mkdir(parents=True)
            canonical_test = canonical / "test_red.py"
            canonical_test.write_text(
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_red(self):\n"
                "        self.fail('canonical planted')\n",
                encoding="utf-8",
            )
            canonical_blocked = run_hook("git commit -m x", str(repo))
            self.assertEqual(canonical_blocked.returncode, 2)
            self.assertIn("main/claude/tests", canonical_blocked.stderr)
            canonical_test.unlink()
            self.assertEqual(run_hook("git commit -m x", str(repo)).returncode, 0)

    def test_commit_gate_runs_the_suite_on_a_modern_interpreter(self) -> None:
        # 2026-07-27: the gate ran the suite on `sys.executable`, i.e. the agent
        # process's `python3`. On a machine where that was 3.9.6 every module
        # died on `import tomllib`, so a green suite reported RED and no commit
        # could land. A planted suite that imports tomllib passes only if the
        # gate resolved >= 3.11; an unusable AGENT_HARNESS_PYTHON must be
        # stepped over rather than blocking, and a floor nothing can meet must
        # say so instead of claiming the suite is red.
        hook = ROOT / "main/claude/hooks/commit-test-gate.py"

        def run_hook(cwd: str, env: dict[str, str] | None = None):
            payload = json.dumps({"tool_input": {"command": "git commit -m x"}, "cwd": cwd})
            return subprocess.run(
                [sys.executable, str(hook)], input=payload,
                capture_output=True, text=True, timeout=120,
                env={**os.environ, **(env or {})},
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            tests = repo / ".claude" / "tests"
            tests.mkdir(parents=True)
            (tests / "test_needs_tomllib.py").write_text(
                "import tomllib, unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_parses(self):\n"
                "        self.assertEqual(tomllib.loads('a = 1'), {'a': 1})\n",
                encoding="utf-8",
            )
            # Resolving the interpreter for `unittest` alone left the suite half
            # upgraded: tests that spawn `#!/usr/bin/env python3` scripts still
            # resolved through PATH onto the old python (this is the shape of
            # the experience-ledger scripts, and it kept the gate red).
            spawned = repo / "spawned-tool"
            spawned.write_text(
                "#!/usr/bin/env python3\n"
                "import tomllib\n"
                "print(tomllib.loads('a = 1')['a'])\n",
                encoding="utf-8",
            )
            spawned.chmod(0o755)
            (tests / "test_spawns_shebang.py").write_text(
                "import subprocess, unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_shebang_child_matches_the_runner(self):\n"
                f"        out = subprocess.run([{str(spawned)!r}],\n"
                "            capture_output=True, text=True)\n"
                "        self.assertEqual(out.returncode, 0, out.stderr)\n"
                "        self.assertEqual(out.stdout.strip(), '1')\n",
                encoding="utf-8",
            )
            self.assertEqual(run_hook(str(repo)).returncode, 0)

            # A pointed-at interpreter that cannot meet the floor is skipped,
            # not obeyed: the override is a hint, not a way to disarm the gate.
            stub = Path(temp_dir) / "too-old"
            stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            stub.chmod(0o755)
            self.assertEqual(
                run_hook(str(repo), {"AGENT_HARNESS_PYTHON": str(stub)}).returncode, 0
            )

            # With nothing able to meet the floor the gate still blocks, but
            # names the interpreter rather than the suite — a subprocess cannot
            # reach this branch because its own `sys.executable` always
            # qualifies, so drive `main` in-process with the search starved.
            import importlib.util
            import io
            from unittest import mock

            spec = importlib.util.spec_from_file_location("commit_test_gate_probe", hook)
            gate = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gate)

            self.assertIsNotNone(gate.suite_interpreter())
            payload = json.dumps(
                {"tool_input": {"command": "git commit -m x"}, "cwd": str(repo)}
            )
            stderr = io.StringIO()
            with mock.patch.object(gate.shutil, "which", return_value=None), \
                    mock.patch.object(gate.sys, "stdin", io.StringIO(payload)), \
                    mock.patch.object(gate.sys, "stderr", stderr):
                self.assertEqual(gate.main(), 2)
            self.assertIn("no Python >=", stderr.getvalue())
            self.assertNotIn("is RED", stderr.getvalue())

    def test_commit_gate_command_prefilters_non_commit_calls(self) -> None:
        # F-03: the PreToolUse gate command must skip the python interpreter
        # entirely when the Bash payload carries no "commit" token, so ordinary
        # commands do not pay a per-call process spawn. A stub hook drops a
        # marker whenever it actually runs.
        settings = json.loads(read(".claude/settings.json"))
        pre = [h["command"] for g in settings["hooks"]["PreToolUse"] for h in g["hooks"]]
        command = next(c for c in pre if "commit-test-gate.py" in c)
        with tempfile.TemporaryDirectory() as temp_home:
            hooks_dir = Path(temp_home) / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            marker = Path(temp_home) / "ran"
            (hooks_dir / "commit-test-gate.py").write_text(
                "import pathlib, sys\n"
                f"pathlib.Path({str(marker)!r}).write_text('x')\n"
                "cmd = __import__('json').load(sys.stdin)['tool_input']['command']\n"
                "sys.exit(2 if 'commit' in cmd else 0)\n",
                encoding="utf-8",
            )
            env = {**os.environ, "HOME": temp_home}

            def run_gate(command_text: str) -> subprocess.CompletedProcess[str]:
                payload = json.dumps({"tool_input": {"command": command_text}})
                return subprocess.run(["sh", "-c", command], input=payload,
                                      capture_output=True, text=True, env=env)

            # Non-commit: exits 0 and never spawns the interpreter.
            self.assertEqual(run_gate("ls -la").returncode, 0)
            self.assertFalse(marker.exists())
            # Commit: the gate runs and its exit code propagates.
            self.assertEqual(run_gate("git commit -m x").returncode, 2)
            self.assertTrue(marker.exists())


if __name__ == '__main__':
    unittest.main()
