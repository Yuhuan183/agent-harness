"""Deterministic mechanisms: hooks, sync preflight, statusline, guards."""
from support import *  # noqa: F401,F403


class MechanismTests(unittest.TestCase):
    def test_statusline_uses_payload_workspace_and_one_jq(self) -> None:
        script = read(".claude/sh/statusline.sh")
        branch = git("branch", "--show-current").stdout.strip()
        payload = {
            "model": {"display_name": "Test"},
            "workspace": {"current_dir": str(ROOT)},
            "cost": {},
            "context_window": {},
        }
        with tempfile.TemporaryDirectory() as other_cwd:
            result = subprocess.run(
                ["bash", str(ROOT / "main/.claude/sh/statusline.sh")],
                cwd=other_cwd,
                input=json.dumps(payload),
                check=True,
                capture_output=True,
                text=True,
            )
        self.assertEqual(script.count("| jq "), 1)
        self.assertIn('git -C "$DIR"', script)
        self.assertIn(ROOT.name, result.stdout)
        if branch:
            self.assertIn(f"({branch})", result.stdout)

    def test_runtime_guard_rejects_old_or_unknown_versions(self) -> None:
        guard = ROOT / "main/.claude/hooks/runtime-guard.py"
        old = subprocess.run([sys.executable, str(guard), "2.1.197 (Claude Code)"],
                             check=True, capture_output=True, text=True)
        current = subprocess.run([sys.executable, str(guard), "2.1.207 (Claude Code)"],
                                 check=True, capture_output=True, text=True)
        unknown = subprocess.run([sys.executable, str(guard), "development build"],
                                 check=True, capture_output=True, text=True)
        self.assertIn("will be blocked", old.stdout)
        self.assertIn("security-reviewer", old.stdout)
        self.assertEqual(current.stdout, "")
        self.assertIn("version unknown", unknown.stdout)

    def test_runtime_guard_gate_blocks_restricted_dispatch(self) -> None:
        guard = ROOT / "main/.claude/hooks/runtime-guard.py"

        def run_gate(version: str, payload: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, str(guard), "--gate", version],
                input=payload, capture_output=True, text=True,
            )

        restricted = '{"tool_name": "Agent", "tool_input": {"subagent_type": "plan-verifier"}}'
        unrestricted = '{"tool_name": "Agent", "tool_input": {"subagent_type": "executor"}}'
        blocked = run_gate("2.1.197 (Claude Code)", restricted)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("blocked plan-verifier dispatch", blocked.stderr)
        unknown = run_gate("development build", restricted)
        self.assertEqual(unknown.returncode, 2)
        # Fail-open paths: supported version, unrestricted role, malformed stdin.
        self.assertEqual(run_gate("2.1.207 (Claude Code)", restricted).returncode, 0)
        self.assertEqual(run_gate("2.1.197 (Claude Code)", unrestricted).returncode, 0)
        self.assertEqual(run_gate("2.1.197 (Claude Code)", "not json").returncode, 0)

    def test_weekly_integrity_stamps_only_after_completed_checks(self) -> None:
        hook = ROOT / "main/.claude/hooks/weekly-integrity.py"
        with tempfile.TemporaryDirectory() as temp_home:
            claude_dir = Path(temp_home) / ".claude"
            scripts_dir = claude_dir / "scripts"
            scripts_dir.mkdir(parents=True)
            report = scripts_dir / "delegation-report"
            report.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            report.chmod(0o755)
            # Both routing resolvers present and green: coverage is complete.
            claude_routing = scripts_dir / "model-routing"
            claude_routing.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            claude_routing.chmod(0o755)
            codex_routing = Path(temp_home) / ".codex" / "scripts" / "model-routing"
            codex_routing.parent.mkdir(parents=True)
            codex_routing.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            codex_routing.chmod(0o755)
            experience_report = (Path(temp_home) / ".agents" / "skills" /
                                 "experience-ledger" / "scripts" / "experience-report")
            experience_report.parent.mkdir(parents=True)
            experience_report.write_text(
                "#!/bin/sh\necho 'no records; log dispatches first'\n",
                encoding="utf-8",
            )
            experience_report.chmod(0o755)
            env = {**os.environ, "HOME": temp_home}
            stamp = claude_dir / "telemetry" / ".integrity-last-run"

            # rsync-deployed ~/.claude (no .git): drift vs the repo copy is
            # reported, but the check completes and the throttle advances.
            repo = Path(temp_home) / "repo"
            (repo / "main" / ".claude").mkdir(parents=True)
            (repo / "main" / ".claude" / "CLAUDE.contract.md").write_text(
                "contract\n", encoding="utf-8")
            (repo / "scripts").mkdir()
            (repo / "scripts/deployment-manifest.tsv").write_text(
                "main/.claude/CLAUDE.contract.md\t.claude/CLAUDE.md\n",
                encoding="utf-8",
            )
            env["AGENT_HARNESS_REPO"] = str(repo)
            drifted = subprocess.run([sys.executable, str(hook)], env=env,
                                     check=True, capture_output=True, text=True)
            self.assertIn("deployment drift", drifted.stdout)
            self.assertIn("dispatch-experience gap", drifted.stdout)
            self.assertNotIn("check failed", drifted.stdout)
            self.assertTrue(stamp.exists())

            # Missing harness checkout: drift monitoring is unavailable — the
            # hook must say so and must NOT advance the throttle stamp.
            stamp.unlink()
            env["AGENT_HARNESS_REPO"] = str(Path(temp_home) / "missing")
            missing = subprocess.run([sys.executable, str(hook)], env=env,
                                     check=True, capture_output=True, text=True)
            self.assertIn("deployment drift check unavailable", missing.stdout)
            self.assertIn("AGENT_HARNESS_REPO", missing.stdout)
            self.assertFalse(stamp.exists())

            # Missing routing resolver: incomplete coverage is a finding, and
            # the throttle stamp must be withheld (F-05: no silent skips).
            env["AGENT_HARNESS_REPO"] = str(repo)
            codex_routing.unlink()
            unresolved = subprocess.run([sys.executable, str(hook)], env=env,
                                        check=True, capture_output=True, text=True)
            self.assertIn("resolver unavailable", unresolved.stdout)
            self.assertFalse(stamp.exists())
            codex_routing.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            codex_routing.chmod(0o755)

            # ~/.claude as a git checkout keeps the original git-status path.
            subprocess.run(["git", "init", str(claude_dir)], check=True,
                           capture_output=True, text=True)
            completed = subprocess.run([sys.executable, str(hook)], env=env,
                                       check=True, capture_output=True, text=True)
            self.assertNotIn("check failed", completed.stdout)
            self.assertTrue(stamp.exists())

            # A git-managed ~/.claude answers drift only for the .claude
            # targets; .codex/.agents manifest parity must still run and catch
            # drift instead of being skipped wholesale (review F-05).
            stamp.unlink()
            (repo / "main" / ".codex").mkdir()
            (repo / "main" / ".codex" / "AGENTS.contract.md").write_text(
                "agents contract\n", encoding="utf-8")
            (repo / "scripts/deployment-manifest.tsv").write_text(
                "main/.claude/CLAUDE.contract.md\t.claude/CLAUDE.md\n"
                "main/.codex/AGENTS.contract.md\t.codex/AGENTS.md\n",
                encoding="utf-8",
            )
            (Path(temp_home) / ".codex" / "AGENTS.md").write_text(
                "drifted\n", encoding="utf-8")
            git_managed_drift = subprocess.run(
                [sys.executable, str(hook)], env=env,
                check=True, capture_output=True, text=True)
            self.assertIn("deployment drift", git_managed_drift.stdout)
            self.assertIn(".codex/AGENTS.md", git_managed_drift.stdout)
            self.assertNotIn("check failed", git_managed_drift.stdout)
            self.assertTrue(stamp.exists())

    def test_sync_and_weekly_integrity_share_one_deployment_manifest(self) -> None:
        hook = read(".claude/hooks/weekly-integrity.py")
        sync = read("scripts/sync.sh")
        pairs = deployment_manifest()
        entries = deployment_manifest_entries()
        sources = [source for source, _ in pairs]
        targets = [target for _, target in pairs]
        self.assertEqual(len(sources), len(set(sources)))
        self.assertEqual(len(targets), len(set(targets)))
        self.assertIn("deployment-manifest.tsv", hook)
        self.assertIn("deployment-manifest.tsv", sync)
        self.assertNotIn("cross_platform =", hook)
        self.assertIn(("main/.claude/CLAUDE.contract.md", ".claude/CLAUDE.md"), pairs)
        self.assertIn(("main/.codex/AGENTS.contract.md", ".codex/AGENTS.md"), pairs)
        self.assertIn(("main/.agents/skills", ".agents/skills", "merge"), entries)
        for source, target in pairs:
            self.assertTrue((ROOT / source).exists(), source)
            self.assertRegex(target, r"^\.(agents|claude|codex)/")

    def test_sync_rejects_unknown_arguments_and_dry_run_preflights(self) -> None:
        sync = ROOT / "scripts/sync.sh"
        unknown = subprocess.run(
            [str(sync), "--unknown"], capture_output=True, text=True,
        )
        self.assertEqual(unknown.returncode, 2)
        self.assertIn("unknown argument", unknown.stderr)

        with tempfile.TemporaryDirectory() as temp_home:
            result = subprocess.run(
                [str(sync)], capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("preflight: passed", result.stdout)
        self.assertIn("dry-run complete", result.stdout)
        # Hooks must land before the settings.json that registers them —
        # settings activate immediately, and a registered-but-missing hook
        # file bricks every guarded tool call (observed 2026-07-23).
        actions = [l for l in result.stdout.splitlines() if "rsync" in l]
        hook_idx = next(i for i, l in enumerate(actions) if "/hooks" in l)
        settings_idx = next(i for i, l in enumerate(actions) if "settings.json" in l)
        self.assertLess(hook_idx, settings_idx,
                        "settings.json must deploy after hook files")

        with tempfile.TemporaryDirectory() as temp_home:
            for platform in (".claude", ".codex", ".agents"):
                unrelated = Path(temp_home) / platform / "skills/unrelated/SKILL.md"
                unrelated.parent.mkdir(parents=True)
                unrelated.write_text("user-owned\n", encoding="utf-8")
            applied = subprocess.run(
                [str(sync), "--apply"], capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertIn("backup: none (no existing managed targets)", applied.stdout)
            self.assertEqual(
                (Path(temp_home) / ".claude/CLAUDE.md").read_text(encoding="utf-8"),
                read(".claude/CLAUDE.contract.md"),
            )
            self.assertEqual(
                (Path(temp_home) / ".codex/AGENTS.md").read_text(encoding="utf-8"),
                read(".codex/AGENTS.contract.md"),
            )
            self.assertTrue(
                (Path(temp_home) / ".codex/skills/experience-ledger/SKILL.md").is_file()
            )
            for source_rel, target_rel, mode in deployment_manifest_entries():
                source = ROOT / source_rel
                target = Path(temp_home) / target_rel
                if mode == "merge":
                    installed = (source / "INSTALLED.txt").read_text(
                        encoding="utf-8"
                    ).splitlines()
                    self.assertEqual(
                        (target / "INSTALLED.txt").read_text(encoding="utf-8"),
                        (source / "INSTALLED.txt").read_text(encoding="utf-8"),
                    )
                    managed_paths = [(source / name, target / name) for name in installed]
                    for managed_source, managed_target in managed_paths:
                        parity = subprocess.run(
                            ["rsync", "-an", "--links", "--force", "--delete",
                             "--delete-excluded", "--exclude", "__pycache__/",
                             "--exclude", "*.pyc", "--exclude", ".DS_Store",
                             "--itemize-changes", str(managed_source),
                             str(managed_target.parent) + "/"],
                            capture_output=True, text=True,
                        )
                        self.assertEqual(parity.returncode, 0, parity.stderr)
                        self.assertEqual(
                            parity.stdout, "", f"drift: {target_rel}/{managed_source.name}"
                        )
                elif source.is_dir():
                    parity = subprocess.run(
                        ["rsync", "-an", "--links", "--force", "--delete",
                         "--delete-excluded", "--exclude", "__pycache__/",
                         "--exclude", "*.pyc", "--exclude", ".DS_Store",
                         "--itemize-changes", str(source), str(target.parent) + "/"],
                        capture_output=True, text=True,
                    )
                    self.assertEqual(parity.returncode, 0, parity.stderr)
                    self.assertEqual(parity.stdout, "", f"drift: {target_rel}")
                else:
                    self.assertEqual(source.read_bytes(), target.read_bytes(), target_rel)
            self.assertFalse(any(Path(temp_home).rglob("__pycache__")))
            self.assertFalse(any(Path(temp_home).rglob("*.pyc")))
            self.assertFalse(any(Path(temp_home).rglob(".DS_Store")))
            for platform in (".claude", ".codex", ".agents"):
                unrelated = Path(temp_home) / platform / "skills/unrelated/SKILL.md"
                self.assertEqual(unrelated.read_text(encoding="utf-8"), "user-owned\n")

    def test_skill_merge_removes_managed_drift_but_preserves_other_skills(self) -> None:
        sync = ROOT / "scripts/sync.sh"
        with tempfile.TemporaryDirectory() as temp_home:
            skill_root = Path(temp_home) / ".agents/skills"
            stale = skill_root / "headroom-protocol/stale.txt"
            stale.parent.mkdir(parents=True)
            stale.write_text("stale\n", encoding="utf-8")
            unrelated = skill_root / "unrelated/SKILL.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("user-owned\n", encoding="utf-8")
            applied = subprocess.run(
                [str(sync), "--apply"], capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
            self.assertEqual(applied.returncode, 0, applied.stderr + applied.stdout)
            self.assertFalse(stale.exists())
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user-owned\n")
            self.assertEqual(
                (skill_root / "INSTALLED.txt").read_text(encoding="utf-8"),
                read(".agents/skills/INSTALLED.txt"),
            )

    def test_sync_refuses_to_drop_global_settings_array_items(self) -> None:
        sync = ROOT / "scripts/sync.sh"
        with tempfile.TemporaryDirectory() as temp_home:
            settings_path = Path(temp_home) / ".claude/settings.json"
            settings_path.parent.mkdir(parents=True)
            settings = json.loads(read(".claude/settings.json"))
            settings.setdefault("permissions", {}).setdefault("allow", []).append(
                "Bash(user-local-command:*)"
            )
            settings_path.write_text(json.dumps(settings), encoding="utf-8")
            before = settings_path.read_text(encoding="utf-8")
            result = subprocess.run(
                [str(sync), "--apply"], capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("permissions.allow", result.stdout)
            self.assertIn("apply stopped to avoid losing local settings", result.stdout)
            self.assertEqual(settings_path.read_text(encoding="utf-8"), before)
            self.assertFalse((Path(temp_home) / ".codex").exists())

    def test_sync_refuses_first_takeover_of_foreign_contracts(self) -> None:
        # A pre-existing AGENTS.md/CLAUDE.md whose content never appeared in
        # this repo's history is someone else's guidance; apply must stop
        # without --accept-contract-takeover (review F-02).
        sync = ROOT / "scripts/sync.sh"
        with tempfile.TemporaryDirectory() as temp_home:
            foreign = Path(temp_home) / ".codex/AGENTS.md"
            foreign.parent.mkdir(parents=True)
            foreign.write_text("someone else's guidance\n", encoding="utf-8")
            env = {**os.environ, "HOME": temp_home,
                   "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"}
            dry = subprocess.run([str(sync)], capture_output=True, text=True, env=env)
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn("WARN: ~/.codex/AGENTS.md", dry.stdout)
            blocked = subprocess.run([str(sync), "--apply"],
                                     capture_output=True, text=True, env=env)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("--accept-contract-takeover", blocked.stdout)
            self.assertEqual(foreign.read_text(encoding="utf-8"),
                             "someone else's guidance\n")
            accepted = subprocess.run(
                [str(sync), "--apply", "--accept-contract-takeover"],
                capture_output=True, text=True, env=env)
            self.assertEqual(accepted.returncode, 0, accepted.stderr + accepted.stdout)
            self.assertEqual(foreign.read_text(encoding="utf-8"),
                             read(".codex/AGENTS.contract.md"))

    def test_routing_wrappers_gate_python_version_before_tomllib(self) -> None:
        # macOS system python3 is 3.9; tomllib needs 3.11+. The wrapper must
        # fail with the real cause, not misreport routing_core as missing, and
        # sync preflight must stop before anything deeper does (review F-03).
        for path in (".claude/scripts/model-routing", ".codex/scripts/model-routing"):
            body = read(path)
            self.assertLess(body.index("version_info < (3, 11)"),
                            body.index("import routing_core"), path)
        self.assertIn("python3 >= 3.11", read("scripts/sync.sh"))
        self.assertIn("3.11", read("docs/setup.md"))

    def test_usage_report_separates_sources_and_finds_rolling_peak(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            main = root / "project" / "main.jsonl"
            subagent = root / "project" / "session" / "subagents" / "agent.jsonl"
            observer = root / "claude-mem-observer-sessions" / "observer.jsonl"
            for path in (main, subagent, observer):
                path.parent.mkdir(parents=True, exist_ok=True)

            def record(timestamp: str, model: str, tokens: int) -> str:
                return json.dumps({
                    "type": "assistant",
                    "timestamp": timestamp,
                    "message": {"model": model, "usage": {
                        "input_tokens": tokens, "output_tokens": 1,
                        "cache_creation_input_tokens": 2, "cache_read_input_tokens": 3,
                    }},
                })

            main.write_text(record("2026-07-15T00:00:00Z", "claude-sonnet-5", 10) + "\n"
                            + record("2026-07-15T04:30:00Z", "claude-sonnet-5", 20) + "\n",
                            encoding="utf-8")
            subagent.write_text(record("2026-07-15T02:00:00Z", "claude-opus-4-8", 30) + "\n",
                                encoding="utf-8")
            observer.write_text(record("2026-07-15T08:00:00Z", "claude-sonnet-4-5", 40) + "\n",
                                encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "main/.claude/scripts/usage-report"),
                 "--root", str(root), "--days", "2",
                 "--now", "2026-07-16T00:00:00Z", "--json"],
                check=True, capture_output=True, text=True)
            report = json.loads(result.stdout)
        self.assertEqual(report["by_source_model"]["main"]["claude-sonnet-5"]["turns"], 2)
        self.assertEqual(report["by_source_model"]["subagent"]["claude-opus-4-8"]["turns"], 1)
        self.assertEqual(report["by_source_model"]["observer"]["claude-sonnet-4-5"]["turns"], 1)
        self.assertEqual(report["peak_rolling_window"]["turns"], 3)

    def test_usage_report_by_session_ranks_sessions_by_cache_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            heavy = root / "project" / "heavy.jsonl"
            light = root / "project" / "light.jsonl"
            for path in (heavy, light):
                path.parent.mkdir(parents=True, exist_ok=True)

            def record(timestamp: str, cache_read: int) -> str:
                return json.dumps({
                    "type": "assistant",
                    "timestamp": timestamp,
                    "message": {"model": "claude-opus-4-8", "usage": {
                        "input_tokens": 1, "output_tokens": 1,
                        "cache_creation_input_tokens": 1, "cache_read_input_tokens": cache_read,
                    }},
                })

            heavy.write_text(record("2026-07-15T00:00:00Z", 500) + "\n"
                             + record("2026-07-15T01:00:00Z", 500) + "\n", encoding="utf-8")
            light.write_text(record("2026-07-15T00:00:00Z", 10) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "main/.claude/scripts/usage-report"),
                 "--root", str(root), "--days", "2",
                 "--now", "2026-07-16T00:00:00Z", "--by-session", "--json"],
                check=True, capture_output=True, text=True)
            report = json.loads(result.stdout)
        rows = report["by_session"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["session"], "heavy")
        self.assertEqual(rows[0]["turns"], 2)
        self.assertEqual(rows[0]["cache_read_input_tokens"], 1000)
        self.assertLess(rows[1]["cache_read_input_tokens"], rows[0]["cache_read_input_tokens"])



class TrapGraderIntegrityTests(unittest.TestCase):
    """Regressions for the review findings F-02/F-03: graders must not pass
    a run that submits no report, and the canonical TWINS regex must not
    accept prose in the count slot."""

    GRADERS = (
        "evals/traps/s7-false-completion/grade.py",
        "evals/traps/s8-spec-conflict/grade.py",
        "evals/traps/s9-tz-bucketing/grade.py",
    )

    def test_graders_require_a_report(self) -> None:
        for grader in self.GRADERS:
            workdir = str(ROOT / Path(grader).parent / "pristine")
            result = subprocess.run(
                [sys.executable, str(ROOT / grader), "--workdir", workdir],
                capture_output=True, text=True, timeout=60,
            )
            self.assertNotEqual(result.returncode, 0, grader)
            self.assertIn("--report", result.stderr, grader)

    def test_intent_capture_survives_decimals_in_the_spec_segment(self) -> None:
        sys.path.insert(0, str(ROOT / "main" / ".agents" / "scripts"))
        try:
            import gate_lines
        finally:
            sys.path.pop(0)
        line = ("INTENT: code does round to 2.67; the check expects 2.68; "
                "the spec says 2.675 rounds to 2.68 via half-up. More prose.")
        match = gate_lines.INTENT.search(gate_lines.flatten(line))
        self.assertIsNotNone(match)
        self.assertIn("half-up", match.group(1))
        paren = ("INTENT: code does X; the check expects Y; "
                 "the spec (README) says half-up rounding.")
        self.assertIsNotNone(gate_lines.INTENT.search(gate_lines.flatten(paren)))

    def test_twins_regex_rejects_non_numeric_counts(self) -> None:
        sys.path.insert(0, str(ROOT / "main" / ".agents" / "scripts"))
        try:
            import gate_lines
        finally:
            sys.path.pop(0)
        good = ("TWINS: searched round( - found 2 other sites: a.py, b.py",
                "TWINS: searched round( — found none other sites.",
                "TWINS: searched x - found 1 other site: utils.py")
        bad = ("TWINS: searched round( - found bananas other sites",
               "TWINS: searched round( - found some other sites")
        for line in good:
            self.assertTrue(gate_lines.TWINS.search(gate_lines.flatten(line)), line)
        for line in bad:
            self.assertFalse(gate_lines.TWINS.search(gate_lines.flatten(line)), line)


if __name__ == '__main__':
    unittest.main()
