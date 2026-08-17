"""Deterministic mechanisms: hooks, sync preflight, statusline, guards."""
import shutil

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
                ["bash", str(ROOT / "main/claude/sh/statusline.sh")],
                cwd=other_cwd,
                input=json.dumps(payload),
                check=True,
                capture_output=True,
                text=True,
            )
        self.assertEqual(script.count("| jq "), 1)
        self.assertIn('git -C "$DIR"', script)
        # The claim under test is that the label comes from the payload
        # workspace and not the process cwd (a temp dir here). *Which* label is
        # the script's own choice: it prefers the origin remote's repo name and
        # falls back to the directory basename. Asserting ROOT.name alone made
        # this pass only where the checkout is named after the repo — in a git
        # worktree the two differ, and the test failed on a statusline that was
        # behaving correctly.
        remote = git("remote", "get-url", "origin").stdout.strip()
        expected = {ROOT.name}
        if remote:
            expected.add(remote.removesuffix(".git").rsplit("/", 1)[-1])
        self.assertTrue(
            any(name in result.stdout for name in expected),
            f"statusline named none of {sorted(expected)}: {result.stdout!r}",
        )
        if branch:
            self.assertIn(f"({branch})", result.stdout)

    def test_compact_reseed_injects_reminder_only_after_compaction(self) -> None:
        hook = ROOT / "main/claude/hooks/compact-reseed.py"

        def run(raw: str):
            return subprocess.run([sys.executable, str(hook)], input=raw,
                                  capture_output=True, text=True)

        # After compaction: injects a SessionStart additionalContext reminder.
        after = run(json.dumps({"hook_event_name": "SessionStart", "source": "compact"}))
        self.assertEqual(after.returncode, 0)
        out = json.loads(after.stdout)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("DECISION:", out["hookSpecificOutput"]["additionalContext"])

        # Other sources, the wrong event, and malformed input stay fail-open:
        # no output, exit 0. This hook must never block a session from starting.
        for raw in (
            json.dumps({"hook_event_name": "SessionStart", "source": "startup"}),
            json.dumps({"hook_event_name": "SessionStart", "source": "resume"}),
            json.dumps({"hook_event_name": "PreToolUse", "source": "compact"}),
            "not json at all",
        ):
            r = run(raw)
            self.assertEqual(r.returncode, 0, raw)
            self.assertEqual(r.stdout.strip(), "", raw)

    def test_compact_reseed_is_registered_on_sessionstart_compact(self) -> None:
        settings = json.loads(read(".claude/settings.json"))
        matchers = [
            m for m in settings["hooks"]["SessionStart"]
            if m.get("matcher") == "compact"
            and any("compact-reseed.py" in h["command"] for h in m["hooks"])
        ]
        self.assertEqual(len(matchers), 1,
                         "compact-reseed must be registered on SessionStart[compact]")

    def test_runtime_guard_rejects_old_or_unknown_versions(self) -> None:
        guard = ROOT / "main/claude/hooks/runtime-guard.py"
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

    def test_runtime_guard_cache_invalidates_on_same_second_binary_swap(self) -> None:
        # A same-second in-place upgrade changes size but not integer mtime;
        # the fingerprint (mtime_ns + size) must still re-probe (G-01).
        import importlib.util
        guard = ROOT / "main/claude/hooks/runtime-guard.py"
        with tempfile.TemporaryDirectory() as tmp:
            binp = Path(tmp) / "claude"

            def write_bin(ver: str) -> None:
                binp.write_text(f'#!/bin/sh\necho "{ver} (Claude Code)"\n')
                binp.chmod(0o755)

            write_bin("2.1.100")
            spec = importlib.util.spec_from_file_location("rg_probe", guard)
            rg = importlib.util.module_from_spec(spec)
            old_argv = sys.argv
            sys.argv = ["rg_probe"]
            try:
                spec.loader.exec_module(rg)
            except SystemExit:
                pass
            finally:
                sys.argv = old_argv
            rg.CACHE = str(Path(tmp) / "cache")
            env_path = os.environ["PATH"]
            os.environ["PATH"] = tmp + os.pathsep + env_path
            try:
                first = rg.probe_version()
                write_bin("2.1.9999")  # longer string -> different size, same second
                second = rg.probe_version()
            finally:
                os.environ["PATH"] = env_path
            self.assertIn("2.1.100", first)
            self.assertIn("2.1.9999", second)

    def test_runtime_guard_gate_blocks_restricted_dispatch(self) -> None:
        guard = ROOT / "main/claude/hooks/runtime-guard.py"

        def run_gate(version: str, payload: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, str(guard), "--gate", version],
                input=payload, capture_output=True, text=True,
            )

        restricted = '{"tool_name": "Agent", "tool_input": {"subagent_type": "plan-verifier"}}'
        # verifier's no-write boundary rides the same runtime enforcement
        # (harness-review F-01).
        verifier = '{"tool_name": "Agent", "tool_input": {"subagent_type": "verifier"}}'
        unrestricted = '{"tool_name": "Agent", "tool_input": {"subagent_type": "executor"}}'
        blocked = run_gate("2.1.197 (Claude Code)", restricted)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("blocked plan-verifier dispatch", blocked.stderr)
        blocked_verifier = run_gate("2.1.197 (Claude Code)", verifier)
        self.assertEqual(blocked_verifier.returncode, 2)
        self.assertIn("blocked verifier dispatch", blocked_verifier.stderr)
        self.assertEqual(run_gate("2.1.207 (Claude Code)", verifier).returncode, 0)
        unknown = run_gate("development build", restricted)
        self.assertEqual(unknown.returncode, 2)
        # Fail-open paths: supported version, unrestricted role, malformed stdin.
        self.assertEqual(run_gate("2.1.207 (Claude Code)", restricted).returncode, 0)
        self.assertEqual(run_gate("2.1.197 (Claude Code)", unrestricted).returncode, 0)
        self.assertEqual(run_gate("2.1.197 (Claude Code)", "not json").returncode, 0)

    def test_leaf_redispatch_gate_uses_the_caller_identity(self) -> None:
        hook = ROOT / "main/claude/hooks/leaf-redispatch.py"

        def run(payload: object) -> subprocess.CompletedProcess[str]:
            raw = payload if isinstance(payload, str) else json.dumps(payload)
            return subprocess.run(
                [sys.executable, str(hook)],
                input=raw, capture_output=True, text=True,
            )

        main_dispatch = run({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "executor"},
        })
        self.assertEqual(main_dispatch.returncode, 0)
        self.assertEqual(main_dispatch.stderr, "")

        leaf_dispatch = run({
            "tool_name": "Agent",
            "agent_type": "executor",
            "tool_input": {"subagent_type": "explore"},
        })
        self.assertEqual(leaf_dispatch.returncode, 2)
        self.assertIn("leaf agent 'executor' cannot dispatch another agent",
                      leaf_dispatch.stderr)
        self.assertIn("Return the proposed dispatch to the main session",
                      leaf_dispatch.stderr)

        # Unknown input cannot be identified as an Agent call, and a malformed
        # tool_input on an unrelated tool must not disturb that tool.
        self.assertEqual(run("not json").returncode, 0)
        unrelated = run({
            "tool_name": "Bash",
            "agent_type": "executor",
            "tool_input": "malformed",
        })
        self.assertEqual(unrelated.returncode, 0)
        self.assertEqual(unrelated.stderr, "")

    def test_leaf_redispatch_gate_is_first_on_agent_pretooluse(self) -> None:
        settings = json.loads(read(".claude/settings.json"))
        agent_hooks = next(
            group["hooks"] for group in settings["hooks"]["PreToolUse"]
            if group.get("matcher") == "Agent"
        )
        commands = [hook["command"] for hook in agent_hooks]
        self.assertIn("leaf-redispatch.py", commands[0])
        self.assertEqual(sum("leaf-redispatch.py" in command
                             for command in commands), 1)

    def test_weekly_integrity_stamps_only_after_completed_checks(self) -> None:
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
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
                "#!/bin/sh\n"
                "echo '{\"by_cohort_provider\": {}, \"hints\": {}, "
                "\"hints_insufficient\": []}'\n",
                encoding="utf-8",
            )
            experience_report.chmod(0o755)
            env = {**os.environ, "HOME": temp_home}
            stamp = claude_dir / "telemetry" / ".integrity-last-run"

            # rsync-deployed ~/.claude (no .git): drift vs the repo copy is
            # reported, but the check completes and the throttle advances.
            repo = Path(temp_home) / "repo"
            (repo / "main" / "claude").mkdir(parents=True)
            (repo / "main" / "claude" / "CLAUDE.contract.md").write_text(
                "contract\n", encoding="utf-8")
            (repo / "scripts").mkdir()
            (repo / "scripts/deployment-manifest.tsv").write_text(
                "main/claude/CLAUDE.contract.md\t.claude/CLAUDE.md\n",
                encoding="utf-8",
            )
            source_marker = (
                Path(temp_home) / ".agents" / "skills" / ".agent-harness-source"
            )
            source_marker.parent.mkdir(parents=True, exist_ok=True)
            source_marker.write_text(str(repo) + "\n", encoding="utf-8")
            env.pop("AGENT_HARNESS_REPO", None)
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
            # A loggable SubagentStop stub older than a day is an un-reconciled
            # dispatch (completed, never logged); a fresh one is still in flight
            # and must not be flagged (harness-review G-03).
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            pending = Path(temp_home) / ".agents" / "telemetry" / "experience-pending.jsonl"
            pending.parent.mkdir(parents=True, exist_ok=True)
            stale_ts = (now - timedelta(days=2)).isoformat(timespec="seconds")
            fresh_ts = now.isoformat(timespec="seconds")
            pending.write_text(
                json.dumps({"ts": stale_ts, "event": "SubagentStop",
                            "agent_type": "verifier", "agent_id": "x1",
                            "session_id": "s1", "dispatch_id": "s1:x1"}) + "\n"
                + json.dumps({"ts": fresh_ts, "event": "SubagentStop",
                              "agent_type": "executor", "agent_id": "y1",
                              "session_id": "s2", "dispatch_id": "s2:y1"}) + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run([sys.executable, str(hook)], env=env,
                                       check=True, capture_output=True, text=True)
            self.assertNotIn("check failed", completed.stdout)
            self.assertIn("un-reconciled dispatches", completed.stdout)
            self.assertIn("s1:x1", completed.stdout)
            self.assertNotIn("s2:y1", completed.stdout)
            self.assertTrue(stamp.exists())
            pending.unlink()

            # A git-managed ~/.claude answers drift only for the .claude
            # targets; .codex/.agents manifest parity must still run and catch
            # drift instead of being skipped wholesale (review F-05).
            stamp.unlink()
            (repo / "main" / "codex").mkdir()
            (repo / "main" / "codex" / "AGENTS.contract.md").write_text(
                "agents contract\n", encoding="utf-8")
            (repo / "scripts/deployment-manifest.tsv").write_text(
                "main/claude/CLAUDE.contract.md\t.claude/CLAUDE.md\n"
                "main/codex/AGENTS.contract.md\t.codex/AGENTS.md\n",
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

    def test_weekly_integrity_says_nothing_about_a_correctly_deployed_system(self) -> None:
        """A freshly synced HOME must produce no findings at all.

        Every other test here feeds the hook a broken system and asserts that
        the matching finding appears. None of them can catch the opposite
        failure: a check that fires on a system with nothing wrong with it.
        That failure is the more expensive one — this hook runs unattended at
        SessionStart, so a finding nobody can clear becomes background noise and
        the next real one is read as more of the same.

        The fixture is a real `sync.sh --apply` into a temporary HOME rather
        than a synthetic manifest, because the false alarms worth catching live
        in the modes a synthetic manifest never exercises: merged targets that
        legitimately carry machine keys, the per-skill merge root, and bytecode
        the deployed scripts regenerate as they run.
        """
        with tempfile.TemporaryDirectory() as temp_home:
            applied = subprocess.run(
                [str(ROOT / "scripts/sync.sh"), "--apply"],
                capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
            self.assertEqual(applied.returncode, 0, applied.stderr + applied.stdout)

            # One reviewed outcome inside the reporting window. An empty ledger
            # means the log loop is not running at all, which is a real finding
            # (asserted separately); it is not the state of a working machine.
            ledger = Path(temp_home) / ".agents/telemetry/experience.jsonl"
            ledger.parent.mkdir(parents=True, exist_ok=True)
            ledger.write_text(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "schema": 3, "role": "explore", "task_class": "recon",
                "provider": "claude", "request_source": "claude-code",
                "outcome": "accepted", "profile": "default",
                "model": "claude-sonnet-5", "effort": "low",
                "route_source": "explicit",
            }) + "\n", encoding="utf-8")

            env = {**os.environ, "HOME": temp_home,
                   "AGENT_HARNESS_REPO": str(ROOT)}
            # The ledger paths are read from HOME; an inherited override would
            # point the hook at this machine's real telemetry.
            env.pop("AGENT_EXPERIENCE_LEDGER", None)
            env.pop("AGENT_EXPERIENCE_PENDING", None)
            result = subprocess.run(
                [sys.executable, str(ROOT / "main/claude/hooks/weekly-integrity.py")],
                env=env, check=True, capture_output=True, text=True,
            )
            self.assertEqual(result.stdout, "", result.stdout)
            self.assertTrue(
                (Path(temp_home) / ".claude/telemetry/.integrity-last-run").exists()
            )

    def test_weekly_integrity_surfaces_withdrawn_skills_and_withdrawn_rows(self) -> None:
        """The drift check must not go blind the moment a row is withdrawn.

        Every parity check here is keyed on a manifest row, so the two states a
        withdrawal leaves behind were the two it could not report: a skill still
        deployed under the shared root after leaving `INSTALLED.txt` (the
        per-skill comparison only walks the skills still listed), and a whole
        tree still deployed after its row was deleted (nothing iterates it at
        all). Both are what sync now retires, and this hook is the layer that
        notices when a machine has not run that sync yet.
        """
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            applied = subprocess.run(
                [str(ROOT / "scripts/sync.sh"), "--apply"],
                capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
            self.assertEqual(applied.returncode, 0, applied.stderr + applied.stdout)

            ghost_skill = home / ".agents/skills/ghost-skill/SKILL.md"
            ghost_skill.parent.mkdir(parents=True, exist_ok=True)
            ghost_skill.write_text("ghost\n", encoding="utf-8")
            ghost_root = home / ".claude/ghost-tool/legacy.py"
            ghost_root.parent.mkdir(parents=True, exist_ok=True)
            ghost_root.write_text("ghost\n", encoding="utf-8")
            inventory = home / ".agents/.deployed-files.tsv"
            with inventory.open("a", encoding="utf-8") as handle:
                handle.write(".agents/skills\t.agents/skills/ghost-skill/SKILL.md\n")
                handle.write(".claude/ghost-tool\t.claude/ghost-tool/legacy.py\n")

            env = {**os.environ, "HOME": temp_home,
                   "AGENT_HARNESS_REPO": str(ROOT)}
            env.pop("AGENT_EXPERIENCE_LEDGER", None)
            env.pop("AGENT_EXPERIENCE_PENDING", None)
            result = subprocess.run(
                [sys.executable, str(ROOT / "main/claude/hooks/weekly-integrity.py")],
                env=env, check=True, capture_output=True, text=True,
            )
            self.assertIn(".agents/skills/ghost-skill/SKILL.md", result.stdout)
            self.assertIn(".claude/ghost-tool/legacy.py", result.stdout)

    def test_weekly_integrity_surfaces_model_alias_drift(self) -> None:
        # The alias->generation assertion is only worth making if something
        # runs it unprompted: a CLI generation move is silent, and every
        # dispatch logged in the meantime names a model that never ran.
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
        with tempfile.TemporaryDirectory() as temp_home:
            scripts_dir = Path(temp_home) / ".claude" / "scripts"
            scripts_dir.mkdir(parents=True)
            routing = scripts_dir / "model-routing"
            routing.write_text(
                "#!/bin/sh\n"
                "case \"$1\" in\n"
                "  check-aliases) echo 'DRIFT: opus: alias moved generation' >&2; exit 1;;\n"
                "  *) exit 0;;\n"
                "esac\n",
                encoding="utf-8",
            )
            routing.chmod(0o755)
            env = {**os.environ, "HOME": temp_home,
                   "AGENT_HARNESS_REPO": str(Path(temp_home) / "repo")}
            result = subprocess.run([sys.executable, str(hook)], env=env,
                                    check=True, capture_output=True, text=True)
        self.assertIn("model-routing alias drift", result.stdout)
        self.assertIn("alias moved generation", result.stdout)
        # Drift is a finding to relay, not a resolver failure.
        self.assertNotIn("alias check failed", result.stdout)

    def test_weekly_integrity_surfaces_overdue_benchmark_priors(self) -> None:
        """`prior_review` needs a scheduled reader or it is only a note.

        Both routing files say to re-audit the AA priors 90 days after as_of.
        That sentence lives inside the config it governs, so nothing was ever
        going to read it on the 91st day: as_of would age quietly while the
        routes went on citing it as current evidence. This hook is the reader.
        """
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
        stub = (
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  check-priors) echo 'priors are 120 days old (cadence 90)' >&2; exit 1;;\n"
            "  *) exit 0;;\n"
            "esac\n"
        )
        for provider in (".claude", ".codex"):
            with tempfile.TemporaryDirectory() as temp_home:
                scripts_dir = Path(temp_home) / provider / "scripts"
                scripts_dir.mkdir(parents=True)
                routing = scripts_dir / "model-routing"
                routing.write_text(stub, encoding="utf-8")
                routing.chmod(0o755)
                result = subprocess.run(
                    [sys.executable, str(hook)],
                    env={**os.environ, "HOME": temp_home,
                         "AGENT_HARNESS_REPO": str(Path(temp_home) / "repo")},
                    check=True, capture_output=True, text=True,
                )
            self.assertIn("benchmark priors overdue", result.stdout, provider)
            self.assertIn("120 days old", result.stdout, provider)
            # Overdue is a finding to relay, not a broken resolver.
            self.assertNotIn("prior-review check failed", result.stdout, provider)

    def test_un_reconciled_dispatches_are_judged_against_the_ledger(self) -> None:
        """Only a stub the ledger has no record of counts as un-reconciled.

        The check used to read the pending file alone and report every stop
        older than a day. `experience-log --from-pending` consumes the stub, but
        logging with explicit flags is equally valid and leaves it behind, so
        every dispatch logged that way was reported forever — under a message
        asserting its outcome was "never logged", while the ledger held that
        exact dispatch id. Acting on it would have duplicated the record.

        A stub with no dispatch id predates the field and cannot be reconciled
        by the command the finding recommends, so it is not reported either.

        An agent type this harness does not route is reported all the same.
        Keying the report on `experience-log`'s enum made "the logger would
        refuse this" mean "say nothing", so a real dispatch of a real agent —
        `claude-code-guide` on this machine, staged, completed, absent from the
        ledger for eleven days — was invisible to every command and every
        report at once (2026-08-06 review). The role picks the remedy, not
        whether the operator hears about it.
        """
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
        old = "2020-01-01T00:00:00+00:00"  # comfortably past the 24h cutoff
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            (home / ".agents/telemetry").mkdir(parents=True)
            pending = home / ".agents/telemetry/experience-pending.jsonl"
            ledger = home / ".agents/telemetry/experience.jsonl"
            stub = {"event": "SubagentStop", "agent_type": "mech-executor", "ts": old}
            unrouted = {"event": "SubagentStop", "agent_type": "claude-code-guide",
                        "ts": old}
            pending.write_text("\n".join(json.dumps(row) for row in [
                {**stub, "dispatch_id": "sess:logged-explicitly"},
                {**stub, "dispatch_id": "sess:never-logged"},
                {**stub},  # pre-migration stub: no dispatch id at all
                {**unrouted, "dispatch_id": "sess:unrouted-role"},
            ]) + "\n", encoding="utf-8")
            ledger.write_text(json.dumps(
                {"role": "mech-executor", "outcome": "accepted",
                 "dispatch_id": "sess:logged-explicitly"}) + "\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(hook)],
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_REPO": str(home / "repo")},
                check=True, capture_output=True, text=True,
            )

        self.assertIn("sess:never-logged", result.stdout)
        self.assertNotIn("sess:logged-explicitly", result.stdout)
        # The id-less stub must not surface as a bare "?" the reader cannot act on.
        un_reconciled = result.stdout.split("un-reconciled dispatches")[-1]
        self.assertNotIn("?", un_reconciled)
        # Reported, and reported with the command that can actually close it:
        # `experience-log` refuses a role it does not route, so naming the id
        # under the log instruction alone would be a finding with no exit.
        self.assertIn("sess:unrouted-role", result.stdout)
        self.assertIn("experience-stage --abandon", result.stdout)
        routes_none = result.stdout.split("routes no role for")[-1]
        self.assertIn("sess:unrouted-role", routes_none)
        self.assertNotIn("sess:never-logged", routes_none)

    def test_a_staged_native_codex_launch_is_reconciled_too(self) -> None:
        """Native Codex has no completion hook, so the launch is the carrier.

        Everything else in this check keys on a staged SubagentStop, which only
        a hook writes. A native Codex dispatch that finished and was never
        logged therefore left nothing to find at all — and the ones most likely
        to be dropped are the hard and failed ones, which is precisely the bias
        the ledger must not develop. The dispatcher-staged launch closes that,
        so it has to be read here whether or not a completion follows.
        """
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
        old = "2020-01-01T00:00:00+00:00"
        fresh = datetime.now(timezone.utc).isoformat(timespec="seconds")
        staged = {"event": "SubagentStart", "agent_type": "executor",
                  "request_source": "codex", "ts": old}

        def run(rows, ledger_rows=()):
            with tempfile.TemporaryDirectory() as temp_home:
                home = Path(temp_home)
                (home / ".agents/telemetry").mkdir(parents=True)
                (home / ".agents/telemetry/experience-pending.jsonl").write_text(
                    "".join(json.dumps(row) + "\n" for row in rows),
                    encoding="utf-8")
                (home / ".agents/telemetry/experience.jsonl").write_text(
                    "".join(json.dumps(row) + "\n" for row in ledger_rows),
                    encoding="utf-8")
                return subprocess.run(
                    [sys.executable, str(hook)],
                    env={**os.environ, "HOME": temp_home,
                         "AGENT_HARNESS_REPO": str(home / "repo")},
                    check=True, capture_output=True, text=True).stdout

        # Launched, never logged, no completion staged either: the launch alone
        # has to raise it, which is the case that used to be invisible.
        forgotten = run([{**staged, "dispatch_id": "codex:forgotten"}])
        self.assertIn("un-reconciled dispatches", forgotten)
        # The finding names the way out for a launch that never ran.
        self.assertIn("experience-stage --cancel", forgotten)

        # Both rows staged: one dispatch, reported once.
        completed = run([
            {**staged, "dispatch_id": "codex:forgotten"},
            {**staged, "event": "SubagentStop", "dispatch_id": "codex:forgotten"},
        ])
        self.assertEqual(completed.count("codex:forgotten"), 1)

        # Same dispatch, now in the ledger: the finding must clear.
        logged = run(
            [{**staged, "dispatch_id": "codex:forgotten"}],
            [{"role": "executor", "outcome": "failed",
              "dispatch_id": "codex:forgotten"}],
        )
        self.assertNotIn("codex:forgotten", logged)

        # A Claude launch is not a carrier for this check: its own SubagentStop
        # hook reports it, and flagging in-flight dispatches would put the check
        # in permanent alarm. A staged launch younger than a day is in flight too.
        quiet = run([
            {"event": "SubagentStart", "agent_type": "executor", "ts": old,
             "request_source": "claude-code", "dispatch_id": "sess:in-flight"},
            {**staged, "ts": fresh, "dispatch_id": "codex:just-launched"},
        ])
        self.assertNotIn("un-reconciled dispatches", quiet)

    def test_a_damaged_pending_row_cannot_abort_the_whole_check(self) -> None:
        """One bad byte took the entire integrity report down with it.

        The ledger read was given `errors="replace"` on 2026-07-30; the pending
        read beside it was not, and a UnicodeDecodeError is a ValueError, not an
        OSError — so it escaped the local handler, hit the outer catch-all, and
        the hook printed `check failed unexpectedly` instead of every finding it
        had already collected. The pending file is the one a hook appends to on
        every subagent stop, so it is the likelier of the two to be damaged.
        """
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
        stub = {"event": "SubagentStop", "agent_type": "mech-executor",
                "ts": "2020-01-01T00:00:00+00:00",
                "dispatch_id": "sess:never-logged"}
        # Both files it reads, because they are two separate parsers with the
        # same assumption: the ledger scan reconciles ids, the pending scan
        # finds the stale stubs, and either one aborting takes the whole check
        # down with every finding collected before it.
        for name, damage in JSONL_DAMAGE:
            for target in ("experience-pending.jsonl", "experience.jsonl"):
                with self.subTest(f"{name}/{target}"), \
                        tempfile.TemporaryDirectory() as temp_home:
                    home = Path(temp_home)
                    telemetry = home / ".agents/telemetry"
                    telemetry.mkdir(parents=True)
                    (telemetry / "experience-pending.jsonl").write_bytes(
                        json.dumps(stub).encode("utf-8") + b"\n"
                        + (damage if target.startswith("experience-p") else b""))
                    (telemetry / "experience.jsonl").write_bytes(
                        damage if target == "experience.jsonl" else b"")
                    result = subprocess.run(
                        [sys.executable, str(hook)],
                        env={**os.environ, "HOME": temp_home,
                             "AGENT_HARNESS_REPO": str(home / "repo")},
                        check=True, capture_output=True, text=True)
                    self.assertNotIn("check failed unexpectedly", result.stdout)
                    self.assertIn("sess:never-logged", result.stdout)

    def test_a_crashed_experience_reader_is_reported_not_read_as_no_data(self) -> None:
        """"The reader died" and "there is nothing to report" are opposite facts.

        `report = json.loads(exp.stdout) if exp.returncode == 0 else {}` turned
        the first into the second, and `{}` then took the no-hints branch and
        said nothing. So a ledger row the reader could not handle retired the
        dispatch hints *and* the routing revision behind them in complete
        silence, while this hook went on stamping itself complete
        (2026-08-03 review).
        """
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            scripts = home / ".agents/skills/experience-ledger/scripts"
            scripts.mkdir(parents=True)
            stub = scripts / "experience-report"
            stub.write_text("#!/bin/sh\necho 'boom' >&2\nexit 1\n", encoding="utf-8")
            stub.chmod(0o755)
            (home / ".agents/telemetry").mkdir(parents=True)
            (home / ".agents/telemetry/experience-pending.jsonl").write_bytes(b"")
            result = subprocess.run(
                [sys.executable, str(hook)],
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_REPO": str(home / "repo")},
                check=True, capture_output=True, text=True)
            self.assertIn("dispatch-experience reader failed", result.stdout)
            self.assertIn("boom", result.stdout, "the reader's own error is lost")
            # A check that could not run must not advance the throttle, or the
            # finding disappears for a week.
            self.assertFalse((home / ".claude/telemetry/.integrity-last-run").exists(),
                             "a failed reader still stamped the run complete")

    def test_ledger_damage_reaches_the_weekly_report(self) -> None:
        """Surviving the damage quietly is the failure the fix created.

        Making the reader skip a bad row instead of dying on it turned a loud
        break into a silent shrink: the report still exits 0, the tables are
        just missing rows nobody knows about. So the count the reader now
        publishes has to be read by something. This hook is the only consumer
        that opens the report unasked (2026-08-04 review).

        Informational, and deliberately not throttle-blocking: the check ran
        correctly and it is the ledger file that is damaged, so withholding the
        stamp would re-run a healthy check every session over a fact that will
        not change until someone edits the file.
        """
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            scripts = home / ".agents/skills/experience-ledger/scripts"
            scripts.mkdir(parents=True)
            stub = scripts / "experience-report"
            stub.write_text(
                "#!/bin/sh\nprintf '%s\\n' '{\"unusable_rows\": 3}'\n",
                encoding="utf-8")
            stub.chmod(0o755)
            (home / ".agents/telemetry").mkdir(parents=True)
            (home / ".agents/telemetry/experience-pending.jsonl").write_bytes(b"")
            result = subprocess.run(
                [sys.executable, str(hook)],
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_REPO": str(home / "repo")},
                check=True, capture_output=True, text=True)
            self.assertIn("experience ledger damage: 3 row(s)", result.stdout)

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
        self.assertIn(("main/claude/CLAUDE.contract.md", ".claude/CLAUDE.md"), pairs)
        self.assertIn(("main/codex/AGENTS.contract.md", ".codex/AGENTS.md"), pairs)
        self.assertIn(("main/.agents/skills", ".agents/skills", "merge"), entries)
        for source, target in pairs:
            self.assertTrue((ROOT / source).exists(), source)
            self.assertRegex(target, r"^\.(agents|claude|codex)/")

    def test_harness_sources_are_not_discoverable_while_developing(self) -> None:
        """`main/` is deployment source, never a working environment.

        Claude Code discovers skills, agents, and settings from `.claude/` below
        the working directory — and when an unqualified skill name is invoked it
        also loads the directory-qualified variant covering the files being
        edited. A source tree named `.claude/` therefore gets listed twice and
        loaded twice in every session that edits this repo, competing with the
        deployed copy it exists to produce. The bundles that a CLI discovers are
        stored undotted and regain the dot from the manifest's target column.

        `.agents/` is exempt and must stay dotted: nothing discovers it, and both
        bundles reach the shared skills through relative symlinks that rsync
        copies verbatim, so the shared root has to sit at the same depth and name
        in the repo as in `$HOME`.
        """
        discovered_by_a_cli = {".claude", ".codex"}
        offenders = sorted(
            str(path.relative_to(ROOT))
            for path in (ROOT / "main").rglob("*")
            if path.is_dir() and not path.is_symlink()
            and path.name in discovered_by_a_cli
        )
        self.assertEqual(offenders, [], "discoverable config trees under main/")

        for source, target, _ in deployment_manifest_entries():
            head = target.split("/", 1)[0]
            if head in discovered_by_a_cli:
                self.assertTrue(
                    source.startswith(f"main/{head.lstrip('.')}/"),
                    f"{source} deploys {target} from a discoverable path",
                )
            else:
                self.assertTrue(
                    source.startswith(f"main/{head}/"),
                    f"{source} does not mirror the deployed layout of {target}",
                )

    def test_contract_takeover_guard_accepts_a_contract_this_repo_produced(self) -> None:
        """Updating a contract must not be mistaken for foreign guidance.

        The guard asks whether the deployed CLAUDE.md/AGENTS.md content ever
        appeared in this repo's history. It answered that question with
        `git rev-list ... | grep -q`, where grep exits on the first hit and
        SIGPIPEs the rev-list feeding it; under the script's `pipefail` the
        pipeline reported 141 and every real contract update was flagged as
        content this repo never produced, stopping `--apply`. Nothing caught it
        because the guard short-circuits when the deployed file already matches
        the worktree — the only case the suite exercised.
        """
        sync = ROOT / "scripts/sync.sh"
        contracts = {
            "main/claude/CLAUDE.contract.md": ".claude/CLAUDE.md",
            "main/codex/AGENTS.contract.md": ".codex/AGENTS.md",
        }
        with tempfile.TemporaryDirectory() as temp_home:
            for source, target in contracts.items():
                # A committed revision of our own contract, deliberately not the
                # working-tree one, so the guard takes the history lookup path.
                # Sources moved from `main/.claude` to `main/claude`; ask both,
                # exactly as the guard does, so this passes on either side of
                # that commit rather than only after it lands.
                dotted = source.replace("main/", "main/.", 1)
                historical = (git("show", f"HEAD:{source}").stdout
                              or git("show", f"HEAD:{dotted}").stdout)
                self.assertTrue(historical, source)
                deployed = Path(temp_home) / target
                deployed.parent.mkdir(parents=True, exist_ok=True)
                deployed.write_text(historical, encoding="utf-8")

            result = subprocess.run(
                [str(sync)], capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("content unknown to this repo", result.stdout)
        self.assertNotIn("has content unknown", result.stdout)

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
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1",},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("preflight: passed", result.stdout)
        self.assertIn("dry-run complete", result.stdout)
        # Hooks must land before the settings.json that registers them —
        # settings activate immediately, and a registered-but-missing hook
        # file bricks every guarded tool call (observed 2026-07-23).
        # settings.json deploys via merge-json, which reports itself instead of
        # emitting an rsync line, so match planned actions rather than rsync.
        actions = [l for l in result.stdout.splitlines() if "[dry-run]" in l]
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
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1",},
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
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
                if mode in ("merge-json", "merge-toml"):
                    # A merged target carries machine state the source does not
                    # have, so byte parity is the wrong invariant. Its parity
                    # check is re-merge idempotence, asserted below and enforced
                    # by sync.sh itself before it reports success.
                    merger = ("merge-settings.py" if mode == "merge-json"
                              else "merge-toml.py")
                    verify = subprocess.run(
                        [sys.executable, str(ROOT / "scripts" / merger),
                         str(source), str(target), "--verify"],
                        capture_output=True, text=True,
                    )
                    self.assertEqual(verify.returncode, 0,
                                     f"{target_rel}: {verify.stderr}")
                    continue
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
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1",},
            )
            self.assertEqual(applied.returncode, 0, applied.stderr + applied.stdout)
            self.assertFalse(stale.exists())
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user-owned\n")
            self.assertEqual(
                (skill_root / "INSTALLED.txt").read_text(encoding="utf-8"),
                read(".agents/skills/INSTALLED.txt"),
            )
            self.assertEqual(
                (skill_root / ".agent-harness-source").read_text(
                    encoding="utf-8"
                ).strip(),
                str(ROOT),
            )

    def test_sync_merges_settings_without_dropping_machine_state(self) -> None:
        # settings.json has three writers: this repo, Claude Code itself
        # (`/model`, `/effort`), and third-party hook installers. Deploying it
        # must land the repo's own entries without deleting the other two.
        # End-to-end through sync.sh --apply, not just the merge unit.
        sync = ROOT / "scripts/sync.sh"
        foreign = {
            "type": "command",
            "command": "/bin/sh '/opt/vendor/agent-hooks/vendor-hook.sh'",
            "timeout": 10,
        }
        # Third-party installers use the documented hooks directory, so a
        # vendor hook is indistinguishable from ours by path. Ownership by
        # `$HOME/.claude/hooks/` prefix therefore adopted this one and deleted
        # its whole event on the next deploy (reproduced 2026-07-29).
        resident = {
            "type": "command",
            "command": 'python3 "$HOME/.claude/hooks/vendor.py"',
            "timeout": 10,
        }
        with tempfile.TemporaryDirectory() as temp_home:
            settings_path = Path(temp_home) / ".claude/settings.json"
            settings_path.parent.mkdir(parents=True)
            settings = json.loads(read(".claude/settings.json"))
            settings.setdefault("permissions", {}).setdefault("allow", []).append(
                "Bash(user-local-command:*)"
            )
            settings["model"] = "opus[1m]"
            settings["effortLevel"] = "high"
            # A vendor group in an event the repo owns, and one it does not.
            settings["hooks"]["PreToolUse"].append({"matcher": "*", "hooks": [foreign]})
            settings["hooks"]["UserPromptSubmit"] = [{"hooks": [foreign]}]
            # The same, for a vendor hook that lives in the shared hooks dir:
            # alone in its own event, and appended into a group the repo owns.
            settings["hooks"]["Notification"] = [{"hooks": [resident]}]
            settings["hooks"]["SubagentStop"][0]["hooks"].append(resident)
            # A repo-owned hook left at a stale command must be updated, not
            # duplicated — this is the case a naive merge gets wrong.
            settings["hooks"]["SessionStart"][0]["hooks"][0]["command"] = (
                'python3 "$HOME/.claude/hooks/runtime-guard.py" --stale-flag'
            )
            settings_path.write_text(json.dumps(settings), encoding="utf-8")
            result = subprocess.run(
                [str(sync), "--apply"], capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1",},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            merged = json.loads(settings_path.read_text(encoding="utf-8"))

        commands = [h["command"] for groups in merged["hooks"].values()
                    for g in groups for h in g["hooks"]]
        # Machine state survives.
        self.assertEqual(merged["model"], "opus[1m]")
        self.assertEqual(merged["effortLevel"], "high")
        self.assertIn("Bash(user-local-command:*)", merged["permissions"]["allow"])
        # Foreign hooks survive, in both kinds of event.
        self.assertEqual(sum(foreign["command"] == c for c in commands), 2)
        self.assertIn("UserPromptSubmit", merged["hooks"])
        # And so does one whose command sits in the shared hooks directory:
        # this repo owns the hooks it ships, not the directory they live in.
        self.assertIn("Notification", merged["hooks"])
        self.assertEqual(sum(resident["command"] == c for c in commands), 2,
                         "a vendor hook under ~/.claude/hooks was adopted and "
                         "dropped as if this repo had shipped it")
        # The repo's own stale entry is updated exactly once, not duplicated.
        self.assertNotIn(
            'python3 "$HOME/.claude/hooks/runtime-guard.py" --stale-flag', commands
        )
        repo_settings = json.loads(read(".claude/settings.json"))
        for group in repo_settings["hooks"]["SessionStart"]:
            for hook in group["hooks"]:
                self.assertEqual(sum(hook["command"] == c for c in commands), 1,
                                 hook["command"])

    def test_sync_retires_its_own_files_and_leaves_foreign_ones_alone(self) -> None:
        """Deleting must be driven by what this repo deployed, not by directory.

        `~/.claude/hooks`, `~/.claude/agents`, `~/.claude/scripts` and
        `~/.codex/prompts` are the documented places for *every* installer's
        files, not this repo's territory. The directory-wide `rsync --delete`
        that used to clean them read a vendor's file as a leftover of ours and
        removed it. The replacement is a per-file inventory, which has the
        opposite failure mode — never retiring anything — so both directions
        are asserted here in one real `--apply` fixture.
        """
        sync = ROOT / "scripts/sync.sh"
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            env = {**os.environ, "HOME": temp_home,
                   "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"}
            first = subprocess.run([str(sync), "--apply"], env=env,
                                   capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            inventory = home / ".agents/.deployed-files.tsv"
            self.assertTrue(inventory.exists(), first.stdout)
            recorded = inventory.read_text(encoding="utf-8").splitlines()
            self.assertIn(".claude/hooks\t.claude/hooks/commit-test-gate.py", recorded)
            # An inventory of the shared roots only, or of nothing, would let
            # the prune pass vacuously.
            self.assertGreater(len(recorded), 20, recorded)

            # What a third-party installer leaves in those same directories.
            foreign = [home / ".claude/hooks/vendor.py",
                       home / ".claude/agents/vendor-agent.md",
                       home / ".codex/prompts/vendor-prompt.md"]
            for path in foreign:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("vendor\n", encoding="utf-8")
            # And a file this repo really did deploy once and has since dropped.
            retired = home / ".claude/hooks/retired-hook.py"
            retired.write_text("retired\n", encoding="utf-8")
            with inventory.open("a", encoding="utf-8") as handle:
                handle.write(".claude/hooks\t.claude/hooks/retired-hook.py\n")

            second = subprocess.run([str(sync), "--apply"], env=env,
                                    capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)

            for path in foreign:
                self.assertTrue(path.exists(),
                                f"sync deleted a file it never deployed: {path}")
            self.assertFalse(retired.exists(),
                             "a file this repo deployed and dropped was not retired")
            self.assertIn("retired-hook.py", second.stdout)
            # The retirement must not have been recorded as still deployed.
            self.assertNotIn(
                ".claude/hooks\t.claude/hooks/retired-hook.py",
                inventory.read_text(encoding="utf-8").splitlines(),
            )

    def test_sync_retires_withdrawn_skills_and_withdrawn_manifest_rows(self) -> None:
        """Withdrawing something has to retire it, not orphan it permanently.

        Both prune passes used to be driven by rows that still exist, so the two
        shapes a withdrawal actually takes were the two it could not see:

        * a skill dropped from `INSTALLED.txt` — the shared skill root recorded
          no ownership at all, so there was nothing to prune it from and nothing
          enumerated the deployed root either;
        * a manifest row deleted outright — its prune was never called, and the
          inventory was then rewritten without it, discarding the one record
          that could have retired the tree on any later run.

        Either way the deployed copy stayed live and every layer reported
        success, which for a skill means it keeps loading into every session.
        Asserted in one real `--apply` fixture: first that the ownership is
        recorded at all, then that an inventory entry with no surviving row
        behind it is retired while a file this repo never deployed is not.
        """
        sync = ROOT / "scripts/sync.sh"
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            env = {**os.environ, "HOME": temp_home,
                   "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"}
            first = subprocess.run([str(sync), "--apply"], env=env,
                                   capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            inventory = home / ".agents/.deployed-files.tsv"
            recorded = inventory.read_text(encoding="utf-8").splitlines()
            # The shared skill root is deployed per skill, so it must claim its
            # files per skill; claiming nothing is what made a withdrawn skill
            # unretirable.
            self.assertIn(".agents/skills\t.agents/skills/INSTALLED.txt", recorded)
            self.assertTrue(
                any(line.startswith(".agents/skills\t.agents/skills/")
                    and line.endswith("/SKILL.md") for line in recorded),
                "the shared skill root recorded no per-skill ownership",
            )
            # File rows rename their target, so each one is its own root.
            self.assertIn(".claude/CLAUDE.md\t.claude/CLAUDE.md", recorded)

            # A skill this repo deployed under the shared root and has since
            # dropped from INSTALLED.txt, and a whole target root whose manifest
            # row is gone.
            ghost_skill = home / ".agents/skills/ghost-skill/SKILL.md"
            ghost_skill.parent.mkdir(parents=True, exist_ok=True)
            ghost_skill.write_text("ghost\n", encoding="utf-8")
            ghost_root = home / ".claude/ghost-tool/legacy.py"
            ghost_root.parent.mkdir(parents=True, exist_ok=True)
            ghost_root.write_text("ghost\n", encoding="utf-8")
            with inventory.open("a", encoding="utf-8") as handle:
                handle.write(".agents/skills\t.agents/skills/ghost-skill/SKILL.md\n")
                handle.write(".claude/ghost-tool\t.claude/ghost-tool/legacy.py\n")
            # Never recorded, so never ours, even inside a root we do own.
            foreign = home / ".agents/skills/foreign-note.md"
            foreign.write_text("vendor\n", encoding="utf-8")

            second = subprocess.run([str(sync), "--apply"], env=env,
                                    capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)

            self.assertFalse(
                ghost_skill.exists(),
                "a skill dropped from INSTALLED.txt was left deployed")
            self.assertFalse(
                ghost_root.exists(),
                "a target root the manifest no longer carries was left deployed")
            self.assertTrue(
                foreign.exists(),
                f"sync deleted a file it never deployed: {foreign}")
            still = inventory.read_text(encoding="utf-8").splitlines()
            self.assertNotIn(
                ".agents/skills\t.agents/skills/ghost-skill/SKILL.md", still)
            self.assertNotIn(
                ".claude/ghost-tool\t.claude/ghost-tool/legacy.py", still)

    def test_weekly_integrity_parses_the_real_deployment_manifest(self) -> None:
        # The hook re-implements manifest parsing, so a mode added to the
        # manifest and to sync.sh but not here makes load_deployment_manifest
        # raise, which the hook catches — silently killing the whole deployment
        # drift check while still looking like a normal finding. Every existing
        # test used a synthetic manifest, so `merge-json` shipped broken.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "weekly_integrity_probe",
            ROOT / "main/claude/hooks/weekly-integrity.py",
        )
        module = importlib.util.module_from_spec(spec)
        # The hook body runs checks at import; only the parser is wanted here.
        source = (ROOT / "main/claude/hooks/weekly-integrity.py").read_text(
            encoding="utf-8"
        )
        namespace: dict = {}
        exec(source[:source.index("try:\n    if os.path.exists(STAMP)")], namespace)

        entries = namespace["load_deployment_manifest"](str(ROOT))
        manifest_modes = {mode for _, _, mode in entries}
        self.assertEqual(len(entries), len(deployment_manifest_entries()))
        # Every mode the manifest actually uses must be understood here.
        self.assertIn("merge-json", manifest_modes)
        self.assertIn("merge-toml", manifest_modes)
        self.assertEqual(
            manifest_modes,
            {mode for _, _, mode in deployment_manifest_entries()},
        )

    def test_drift_check_ignores_runtime_generated_bytecode(self) -> None:
        # Deployed scripts write __pycache__ as they run. If the drift check
        # counts that as drift the alarm can never clear, and an alarm that is
        # always on is worse than none. Real drift must still be caught.
        hook = read(".claude/hooks/weekly-integrity.py")
        self.assertIn("--checksum", hook)
        # As an rsync argument, not as prose in the comment explaining why.
        self.assertNotIn('"--delete-excluded"', hook)

        src = ROOT / "main/.agents/scripts"
        with tempfile.TemporaryDirectory() as temp_dir:
            dst_parent = Path(temp_dir)
            subprocess.run(["rsync", "-a", str(src), str(dst_parent) + "/"], check=True)
            deployed = dst_parent / "scripts"
            args = ["rsync", "-a", "--checksum", "--links", "--delete",
                    "--exclude", "__pycache__/", "--exclude", "*.pyc",
                    "--exclude", ".DS_Store", "-n", "--itemize-changes",
                    str(src), str(dst_parent) + "/"]

            def drift() -> list[str]:
                out = subprocess.run(args, capture_output=True, text=True, check=True)
                return [l for l in out.stdout.splitlines()
                        if l and not l.startswith(".") and not l.endswith("/")]

            self.assertEqual(drift(), [])
            # Bytecode the deployed script regenerates: not drift.
            cache = deployed / "__pycache__"
            cache.mkdir(exist_ok=True)
            (cache / "routing_core.cpython-313.pyc").write_bytes(b"\x00bytecode")
            (deployed / ".DS_Store").write_bytes(b"\x00")
            self.assertEqual(drift(), [])
            # A real edit to a deployed file is still caught.
            (deployed / "routing_core.py").write_text("tampered\n", encoding="utf-8")
            self.assertTrue(any("routing_core.py" in l for l in drift()), drift())

    def test_codex_config_merge_preserves_machine_state(self) -> None:
        # ~/.codex/config.toml carries GPT model/effort, MCP, plugins, desktop,
        # shell policy and per-project trust next to the agent registrations
        # this repo owns. Before merge-toml existed the manual step had left 6
        # of 7 roles unregistered with nothing able to notice.
        merge_toml = ROOT / "scripts/merge-toml.py"
        machine = (
            'model = "gpt-5.6-sol"\n'
            'model_reasoning_effort = "high"\n\n'
            "[mcp_servers.example]\n"
            'url = "https://example.invalid/mcp"  # inline comment must survive\n\n'
            "[agents]\n"
            "max_threads = 99\n\n"
            "[agents.verifier]\n"
            'description = "stale wording"\n'
            'config_file = "./agents/verifier.toml"\n\n'
            "[agents.my-own]\n"
            'description = "user agent"\n'
            'config_file = "./agents/mine.toml"\n\n'
            '[projects."<HOME>/repo"]\n'
            'trust_level = "trusted"\n'
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "config.toml"
            config.write_text(machine, encoding="utf-8")
            first = subprocess.run(
                [sys.executable, str(merge_toml),
                 str(ROOT / "main/codex/config.merge.toml"), str(config)],
                capture_output=True, text=True,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            merged = tomllib.loads(config.read_text(encoding="utf-8"))
            text = config.read_text(encoding="utf-8")

            # Re-running must be a no-op; that is also sync.sh's parity check.
            second = subprocess.run(
                [sys.executable, str(merge_toml),
                 str(ROOT / "main/codex/config.merge.toml"), str(config), "--verify"],
                capture_output=True, text=True,
            )
            self.assertEqual(second.returncode, 0, second.stderr)

        declared = tomllib.loads(read(".codex/config.merge.toml"))["agents"]
        role_names = [k for k, v in declared.items() if isinstance(v, dict)]
        # Every repo-declared role is registered, with the repo's wording.
        for role in role_names:
            self.assertIn(role, merged["agents"], role)
            self.assertEqual(merged["agents"][role]["description"],
                             declared[role]["description"], role)
        # Machine state survives: unrelated tables, a user's own agent, an
        # inline comment, and the repo's own [agents] scalars are all intact.
        self.assertEqual(merged["model"], "gpt-5.6-sol")
        self.assertEqual(merged["model_reasoning_effort"], "high")
        self.assertEqual(merged["mcp_servers"]["example"]["url"],
                         "https://example.invalid/mcp")
        self.assertEqual(merged["projects"]["<HOME>/repo"]["trust_level"],
                         "trusted")
        self.assertEqual(merged["agents"]["my-own"]["description"], "user agent")
        self.assertIn("# inline comment must survive", text)
        self.assertEqual(merged["agents"]["max_threads"], declared["max_threads"])

    def test_repo_settings_hooks_are_all_owned_by_the_merge(self) -> None:
        # If a hook group stops being recognised as ours the merge can no
        # longer update it on deploy and it fossilises at whatever the machine
        # last had. Preflight runs this too; asserting it here names the reason.
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/merge-settings.py"),
             str(ROOT / "main/claude/settings.json"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("every hook group", result.stdout)

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
                   "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1",}
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

    def test_routing_wrappers_select_python_311_before_tomllib(self) -> None:
        # macOS system python3 is 3.9; public entrypoints share one selector
        # that can find a versioned Python without shell-profile aliases.
        selector = ROOT / "main/.agents/scripts/python3-run"
        self.assertTrue(os.access(selector, os.X_OK))
        for path in (".claude/scripts/model-routing", ".codex/scripts/model-routing"):
            wrapper = read(path)
            implementation = read(path + ".py")
            self.assertIn("../../.agents/scripts/python3-run", wrapper)
            self.assertLess(implementation.index("version_info < (3, 11)"),
                            implementation.index("import routing_core"), path)
        sync = read("scripts/sync.sh")
        self.assertIn('PYTHON_RUN="$REPO/main/.agents/scripts/python3-run"', sync)
        self.assertNotRegex(sync, r"(?m)^\s*python3(?:\s|$)")
        with tempfile.TemporaryDirectory() as temp_dir:
            selected = Path(temp_dir) / "python3.13"
            selected.symlink_to(sys.executable)
            result = subprocess.run(
                [str(selector), "-c", "import sys; print(sys.version_info.major)"],
                env={"PATH": f"{temp_dir}:/usr/bin:/bin"},
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "3")
        self.assertIn("3.11", read("docs/setup.md"))

    def test_python_selector_propagates_to_env_shebang_children(self) -> None:
        selector = ROOT / "main/.agents/scripts/python3-run"
        with tempfile.TemporaryDirectory() as temp_dir:
            tools = Path(temp_dir)
            (tools / "python3.13").symlink_to(sys.executable)
            child = tools / "child"
            child.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print(sys.version_info[:2])\n",
                encoding="utf-8",
            )
            child.chmod(0o755)
            result = subprocess.run(
                [str(selector), str(child)],
                capture_output=True,
                text=True,
                env={"PATH": f"{temp_dir}:/usr/bin:/bin"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(sys.version_info[:2]))

        for relative in (
            ".agents/skills/experience-ledger/scripts/experience-report",
            ".agents/skills/experience-ledger/scripts/experience-revise",
        ):
            script = read(relative)
            self.assertLess(
                script.index("sys.version_info < (3, 11)"),
                script.index("import routing_core"),
                relative,
            )
            self.assertIn(' / "scripts" / "python3-run"', script, relative)

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
            subagent.write_text(record("2026-07-15T02:00:00Z", "claude-opus-5", 30) + "\n",
                                encoding="utf-8")
            observer.write_text(record("2026-07-15T08:00:00Z", "claude-sonnet-4-5", 40) + "\n",
                                encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "main/claude/scripts/usage-report"),
                 "--root", str(root), "--days", "2",
                 "--now", "2026-07-16T00:00:00Z", "--json"],
                check=True, capture_output=True, text=True)
            report = json.loads(result.stdout)
        self.assertEqual(report["by_source_model"]["main"]["claude-sonnet-5"]["turns"], 2)
        self.assertEqual(report["by_source_model"]["subagent"]["claude-opus-5"]["turns"], 1)
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
                    "message": {"model": "claude-opus-5", "usage": {
                        "input_tokens": 1, "output_tokens": 1,
                        "cache_creation_input_tokens": 1, "cache_read_input_tokens": cache_read,
                    }},
                })

            heavy.write_text(record("2026-07-15T00:00:00Z", 500) + "\n"
                             + record("2026-07-15T01:00:00Z", 500) + "\n", encoding="utf-8")
            light.write_text(record("2026-07-15T00:00:00Z", 10) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "main/claude/scripts/usage-report"),
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

    def test_usage_report_exposes_attention_percentiles_and_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            transcript = root / "project" / "session.jsonl"
            transcript.parent.mkdir(parents=True)

            def record(timestamp: str, input_tokens: int) -> str:
                return json.dumps({
                    "type": "assistant",
                    "timestamp": timestamp,
                    "message": {"model": "claude-opus-5", "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": 1,
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 0,
                    }},
                })

            transcript.write_text(
                record("2026-07-15T00:00:00Z", 100) + "\n"
                + record("2026-07-15T01:00:00Z", 400) + "\n"
                + record("2026-07-15T02:00:00Z", 800) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(ROOT / "main/claude/scripts/usage-report"),
                 "--root", str(root), "--days", "2",
                 "--now", "2026-07-16T00:00:00Z",
                 "--context-window", "1000", "--by-session", "--json"],
                check=True, capture_output=True, text=True,
            )
            report = json.loads(result.stdout)

        attention = report["attention"]["main"]["claude-opus-5"]
        self.assertEqual(attention["context_percent_p50"], 40.0)
        self.assertEqual(attention["context_percent_p95"], 76.0)
        self.assertEqual(attention["attention_level"], "compact")
        self.assertEqual(
            report["attention_policy"]["thresholds_percent"],
            {"watch": 30.0, "checkpoint": 50.0, "compact": 65.0},
        )
        self.assertEqual(report["by_session"][0]["context_tokens_p95"], 760)

    def test_codex_usage_reports_last_turn_attention_not_session_total(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sessions = Path(temp_dir)
            rollout = sessions / "2026" / "07" / "28" / "rollout-test.jsonl"
            rollout.parent.mkdir(parents=True)
            rollout.write_text(json.dumps({
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {"total_tokens": 99_999},
                        "last_token_usage": {
                            "input_tokens": 600,
                            "cached_input_tokens": 100,
                            "output_tokens": 100,
                            "reasoning_output_tokens": 50,
                            "total_tokens": 700,
                        },
                        "model_context_window": 1000,
                    },
                    "rate_limits": {},
                },
            }) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(
                    ROOT / "main/.agents/skills/experience-ledger/scripts/codex-usage"
                ), "--json"],
                env={**os.environ, "CODEX_SESSIONS_DIR": str(sessions)},
                check=True, capture_output=True, text=True,
            )
            report = json.loads(result.stdout)

        self.assertEqual(report["attention"]["tokens"], 700)
        self.assertEqual(report["attention"]["used_percent"], 70.0)
        self.assertEqual(report["attention"]["remaining_tokens"], 300)
        self.assertEqual(report["attention"]["attention_level"], "compact")
        self.assertEqual(report["session_total"]["total_tokens"], 99_999)
        self.assertEqual(
            report["attention_policy"]["thresholds_percent"],
            {"watch": 30.0, "checkpoint": 50.0, "compact": 65.0},
        )

    def _operator_delta_module(self):
        import importlib.util
        path = ROOT / "scripts" / "contract-operator-delta.py"
        spec = importlib.util.spec_from_file_location("contract_operator_delta", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_operator_delta_sees_the_flip_the_phrase_assertions_cannot(self) -> None:
        # The defect class this exists for: every asserted phrase survives and
        # the meaning does not. Here a disjunction becomes a conjunction, which
        # is how upstream v1.3.7 made a disposition unreachable while 255
        # phrase assertions passed verbatim.
        module = self._operator_delta_module()
        before = module.operator_counts("Reject when the claim is stale or unsigned.")
        after = module.operator_counts("Reject when the claim is stale and unsigned.")
        self.assertEqual(before["or"] - after["or"], 1)
        self.assertEqual(after["and"] - before["and"], 1)
        # A dropped scope limiter is the same class and equally invisible.
        kept = module.operator_counts("Deploy only after the user says so.")
        dropped = module.operator_counts("Deploy after the user says so.")
        self.assertEqual(kept["only"] - dropped["only"], 1)

    def test_operator_delta_is_scoped_to_what_a_session_obeys(self) -> None:
        module = self._operator_delta_module()
        for path in ("main/claude/CLAUDE.contract.md",
                     "main/codex/agents/executor.toml",
                     "main/claude/skills/baton-dispatch/SKILL.md"):
            self.assertTrue(module.in_surface(path), path)
        for path in ("docs/research/README.md", "main/claude/tests/support.py"):
            self.assertFalse(module.in_surface(path), path)

    def test_operator_delta_reports_without_blocking(self) -> None:
        # Evidence, not a gate: it has to exit 0 even when operators moved, or
        # the first noisy compression pass gets it disabled.
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "contract-operator-delta.py"),
             "--range", "HEAD~1..HEAD"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("contract operator delta:", result.stdout)


class TrapGraderIntegrityTests(unittest.TestCase):
    """Regressions for the review findings F-02/F-03: graders must not pass
    a run that submits no report, and the canonical TWINS regex must not
    accept prose in the count slot."""

    GRADERS = (
        "evals/traps/s7-false-completion/grade.py",
        "evals/traps/s8-spec-conflict/grade.py",
        "evals/traps/s9-tz-bucketing/grade.py",
        "evals/traps/s10-skill-recall/grade.py",
        "evals/traps/s11-pointer-redundancy/grade.py",
    )

    def test_every_trap_grader_is_registered(self) -> None:
        """A grader nobody lists is a grader nobody notices has rotted.

        The list above was three hard-coded paths, so s10 could have shipped
        without the report-required regression covering it (2026-07-30).
        """
        self.assertEqual(
            {str(Path(grader)) for grader in self.GRADERS},
            {str(path.relative_to(ROOT))
             for path in (ROOT / "evals/traps").glob("*/grade.py")})

    def test_the_selection_trap_surface_matches_the_live_descriptions(self) -> None:
        """A trap graded against a stale routing surface measures nothing.

        s10 asks which skill a description loads, so its fixture is the real
        frontmatters — generated, and checked here the same way the prompt
        census is, because a copy silently stops being the thing under test.
        """
        build = ROOT / "evals/traps/s10-skill-recall/build.py"
        result = subprocess.run([sys.executable, str(build), "--check"],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    TRAP = "evals/traps/s10-skill-recall"
    # What each arm removes, and what it must therefore still carry. One lever
    # per arm except `d`, which is the combination — B and C each came back
    # clean, and reading that as "cut both" is exactly the inference neither
    # arm supports, because the two clauses cover for each other.
    VARIANT_CONTRACTS = {
        "b-trimmed.md": {
            "removes": ("客服信", "公告", "銷售頁", "電子報"),
            "keeps": ("程式碼／log／設定檔", "code/log/config", "改自然一點"),
        },
        "c-no-exclusions.md": {
            "removes": ("程式碼／log／設定檔", "code/log/config", "事實查核"),
            "keeps": ("客服信", "公告", "改自然一點", "de-AI this text"),
        },
        "d-both.md": {
            "removes": ("客服信", "公告", "程式碼／log／設定檔", "code/log/config"),
            "keeps": ("改自然一點", "de-AI this text"),
        },
    }

    def _speak_human_section(self, body: str) -> str:
        """Just the speak-human-tw block.

        Scoping matters: four other descriptions also carry a `不觸發：` line,
        so a whole-file search for that token says nothing about the skill under
        test — it was the first thing to make this test lie.
        """
        _, _, after = body.partition("## speak-human-tw")
        section, _, _ = after.partition("\n## ")
        self.assertTrue(section.strip(), "speak-human-tw section not found")
        return section

    def test_each_selection_trap_variant_removes_what_it_claims_to(self) -> None:
        """An arm that silently equals the control reports no difference, correctly.

        The variants are hand-written against a generated bundle, so a
        regenerated surface can absorb a trim and leave an arm identical to
        pristine. Each arm also has to keep the lever it is *not* testing, or
        two variables move at once and neither result means anything.
        """
        trap = ROOT / self.TRAP
        pristine = self._speak_human_section(
            (trap / "pristine/descriptions.md").read_text(encoding="utf-8"))
        self.assertEqual(
            set(self.VARIANT_CONTRACTS),
            {path.name for path in (trap / "variants").glob("*.md")},
            "a variant exists with no declared contract, or vice versa")
        for name, contract in self.VARIANT_CONTRACTS.items():
            body = (trap / "variants" / name).read_text(encoding="utf-8")
            self.assertNotEqual(body, (trap / "pristine/descriptions.md").read_text(
                encoding="utf-8"), name)
            section = self._speak_human_section(body)
            for token in contract["removes"]:
                self.assertIn(token, pristine, f"pristine lost {token}")
                self.assertNotIn(token, section, f"{name}: still carries {token}")
            for token in contract["keeps"]:
                self.assertIn(token, section, f"{name}: lost {token}, which it "
                                              "was supposed to hold fixed")

    def test_a_variant_removes_a_clause_in_every_language_that_states_it(self) -> None:
        """A bilingual description states some rules twice; a trim must too.

        Measured the hard way (2026-07-30): the first `b-trimmed.md` dropped the
        zh-TW `不觸發：…程式碼／log／設定檔` and left the English `Not for: …
        code/log/config` untouched, so arm B's three precision items tested
        nothing — all three runs cited the surviving English clause by name. A
        half-removed bilingual pair does not weaken the surface, it just makes
        the arm quietly agree with the control.

        `speak-human-tw` is the only description stating its rules in two
        languages, which is why the pair map is short and explicit rather than
        inferred, and why it is checked inside that section only.
        """
        trap = ROOT / self.TRAP
        pairs = {
            "code-and-config": ("程式碼／log／設定檔", "code/log/config"),
            "literal-translation": ("逐字翻譯", "literal translation"),
            "brand-voice": ("模仿特定品牌", "brand-voice mimicry"),
            "fact-checking": ("事實查核", "fact-checking"),
        }
        pristine = self._speak_human_section(
            (trap / "pristine/descriptions.md").read_text(encoding="utf-8"))
        for name, (zh, en) in pairs.items():
            self.assertIn(zh, pristine, f"pristine lost the zh half of {name}")
            self.assertIn(en, pristine, f"pristine lost the en half of {name}")
        for variant_path in sorted((trap / "variants").glob("*.md")):
            section = self._speak_human_section(
                variant_path.read_text(encoding="utf-8"))
            for name, (zh, en) in pairs.items():
                if (zh in section) == (en in section):
                    continue
                kept, dropped = (zh, en) if zh in section else (en, zh)
                self.fail(
                    f"{variant_path.name}: {name} is half-removed — dropped "
                    f"{dropped!r} but kept {kept!r}, so the surface still "
                    "states the rule and the arm tests nothing")

    def test_the_selection_trap_does_not_claim_to_measure_loading(self) -> None:
        """The eval's stated scope has to match what its grader can see.

        The first version of this trap said it measured "whether the routing
        surface loads the right skill at all". It cannot: the brief is a batch
        classification task with every description in the foreground and the
        answer format supplied, and `grade.py` reads `SELECT:` lines, not
        invocation events. `contract-slimming.md` then cited it as the gate for
        description edits, which turned the overclaim into a decision rule
        (2026-07-31 review).

        Narrowing the claim was the fix, so the claim is what needs the gate —
        including the asymmetry that makes the weaker measurement still usable:
        a failing arm refutes a trim, a passing arm does not license one. If a
        rewrite changes this wording, change it here deliberately; do not
        delete the assertion to make a rename pass.
        """
        required = {
            "evals/traps/s10-skill-recall/README.md": (
                "does not observe skill loading",
                "failing arm is strong",
                "passing arm is weak",
            ),
            "evals/traps/s10-skill-recall/GROUND-TRUTH.md": (
                "does not observe skill loading",
                "failing arm is strong",
                "passing arm is weak",
            ),
            "docs/contract-slimming.md": (
                "鑑別度, 不是實際載入行為",
                "失敗是強證據",
                "通過是弱證據",
            ),
        }
        for path, phrases in required.items():
            body = (ROOT / path).read_text(encoding="utf-8")
            # These are wrapped Markdown, so a phrase may straddle a newline.
            # Collapsed whitespace covers the English; removed whitespace covers
            # the zh-TW, where a wrap inserts no space between characters.
            haystacks = (re.sub(r"\s+", " ", body), re.sub(r"\s+", "", body))
            for phrase in phrases:
                self.assertTrue(
                    any(phrase in hay for hay in haystacks),
                    f"{path} no longer states {phrase!r}: the trap measures "
                    "description discriminability under batch classification, "
                    "not skill loading, and every reader of a result needs "
                    "that scope plus the strong/weak asymmetry")

    def test_rung_runner_isolates_the_sample_from_project_and_proxy(self) -> None:
        """The two properties that make a rung sample worth anything.

        Both were learned the hard way on 2026-08-06. The runner exists because
        sampling a second rung otherwise means editing a deployed pin, so it
        must put model and effort on the command line and read the contract
        from the repo rather than from `~/.claude`. And its first live run
        still landed in the proxy log, because clearing `ANTHROPIC_BASE_URL`
        from the child environment does not survive a project settings file
        that sets it again — which this repository's untracked
        `.claude/settings.local.json` does. Asserting the argv shape is cheap;
        asserting that the default run directory is not the repository is the
        one that would have caught the real defect.
        """
        runner = ROOT / "evals/scripts/rung-run.py"
        result = subprocess.run(
            [sys.executable, str(runner), "--role", "explore",
             "--model", "claude-opus-5", "--effort", "xhigh",
             "--prompt", "x", "--dry-run"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(result.stdout)
        for flag, value in (("--model", "claude-opus-5"), ("--effort", "xhigh")):
            self.assertIn(flag, argv)
            self.assertEqual(argv[argv.index(flag) + 1], value)
        # The contract under test is the repo's, not the deployed copy's.
        body = read("main/claude/agents/explore.md").split("---", 2)[2].strip()
        self.assertIn(body, argv)
        # Frontmatter tools become the allowlist, so a read-only role stays one.
        self.assertIn("--allowedTools", argv)
        self.assertNotIn("Bash", argv)
        # Machine state that would otherwise ride along.
        self.assertIn("--strict-mcp-config", argv)
        self.assertIn("--exclude-dynamic-system-prompt-sections", argv)

        source = runner.read_text(encoding="utf-8")
        self.assertIn("ANTHROPIC_BASE_URL", source)
        # A run inside the repository re-inherits the proxy through project
        # settings; the default must be a directory outside every project.
        self.assertIn("tempfile.mkdtemp", source)
        self.assertNotIn("cwd=REPO", source)

    def test_the_selection_grader_exit_zero_means_what_it_claims(self) -> None:
        """Four ways a perfect-looking run reached exit 0 with findings absent.

        The grader's exit code is the whole result of an arm, and its README
        reads it as "eighteen decisions matched and nothing was written". Two
        gaps made that false (2026-07-31 review): the answer loop only walked
        ANSWERS, so a nineteenth `SELECT:` line was collected and never
        checked; and the read-only sweep exempted files by basename, so
        `nested/report.md` and `sub/descriptions.md` were free writes at any
        depth. Each case is asserted on the exit code, not the wording.
        """
        trap = ROOT / self.TRAP
        grader = trap / "grade.py"
        answers = {}
        for line in (trap / "GROUND-TRUTH.md").read_text(encoding="utf-8").split("\n"):
            match = re.match(r"\|\s*(U\d\d)\s*\|\s*([\w-]+)\s*\|", line)
            if match:
                answers[match.group(1)] = match.group(2)
        self.assertEqual(len(answers), 18, "answer table not parsed")
        perfect = "\n".join(f"SELECT: {u} -> {a}" for u, a in answers.items())

        def grade(report: str, extra: str | None = None) -> int:
            with tempfile.TemporaryDirectory() as temp_dir:
                workdir = Path(temp_dir) / "wd"
                shutil.copytree(trap / "pristine", workdir)
                if extra:
                    (workdir / extra).parent.mkdir(parents=True, exist_ok=True)
                    (workdir / extra).write_text("x", encoding="utf-8")
                report_path = Path(temp_dir) / "report.md"
                report_path.write_text(report + "\n", encoding="utf-8")
                return subprocess.run(
                    [sys.executable, str(grader), "--workdir", str(workdir),
                     "--report", str(report_path)],
                    capture_output=True, text=True, timeout=60).returncode

        self.assertEqual(grade(perfect), 0, "the control no longer passes")
        for name, report, extra in (
            ("a nineteenth decision", perfect + "\nSELECT: U19 -> none", None),
            ("a missing decision", perfect.split("\n", 1)[1], None),
            ("report.md in a subdirectory", perfect, "nested/report.md"),
            ("descriptions.md in a subdirectory", perfect, "sub/descriptions.md"),
            ("any other created file", perfect, "notes.txt"),
        ):
            with self.subTest(name):
                self.assertEqual(grade(report, extra), 1,
                                 f"{name} still reaches exit 0")

    # What each grader grades. The rule is "no grader runs without the evidence
    # it judges"; the flag is only how a given fixture spells it. s7-s10 judge a
    # written report against a worked copy, s11 judges an event stream, and
    # asserting the word `--report` across all of them would have forced the
    # newer fixture to grow an argument it has no use for.
    EVIDENCE_FLAG = {
        "evals/traps/s7-false-completion/grade.py": "--report",
        "evals/traps/s8-spec-conflict/grade.py": "--report",
        "evals/traps/s9-tz-bucketing/grade.py": "--report",
        "evals/traps/s10-skill-recall/grade.py": "--report",
        "evals/traps/s11-pointer-redundancy/grade.py": "--events",
    }

    def test_graders_refuse_to_run_without_their_evidence(self) -> None:
        self.assertEqual(set(self.EVIDENCE_FLAG), set(self.GRADERS),
                         "every registered grader must declare what it grades")
        for grader in self.GRADERS:
            with self.subTest(grader=grader):
                result = subprocess.run(
                    [sys.executable, str(ROOT / grader)],
                    capture_output=True, text=True, timeout=60,
                )
                self.assertNotEqual(result.returncode, 0, grader)
                self.assertIn(self.EVIDENCE_FLAG[grader], result.stderr, grader)

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

    def test_a_gate_line_only_counts_at_column_one_as_plain_text(self) -> None:
        """The contract owes the line at column one; the checker accepted it anywhere.

        Every rejected form below used to pass, which is why a recorded
        "format ✓" was measured against a looser rule than the roles were
        given. Wrapped lines still pass: reports wrap, and that was the
        original reason for flattening.
        """
        sys.path.insert(0, str(ROOT / "main" / ".agents" / "scripts"))
        try:
            import gate_lines
        finally:
            sys.path.pop(0)
        body = "code does X; the check expects Y; the spec says Z."
        self.assertIsNotNone(gate_lines.find("INTENT", f"INTENT: {body}"))
        self.assertIsNotNone(gate_lines.find(
            "INTENT", "INTENT: code does X; the check\nexpects Y; the spec says Z."))
        for wrapped in (f"**INTENT: {body}**", f"- INTENT: {body}",
                        f"> INTENT: {body}", f"Some prose INTENT: {body}",
                        f"  INTENT: {body}", f"#### INTENT: {body}"):
            self.assertIsNone(gate_lines.find("INTENT", wrapped), wrapped)
            # Off-template is a distinct diagnosis from absent: a leaf that
            # bolded its line must hear which mistake it made.
            self.assertTrue(gate_lines.off_template("INTENT", wrapped), wrapped)
        self.assertFalse(gate_lines.off_template("INTENT", "no gate line here"))
        self.assertIsNotNone(gate_lines.find("AUTH", 'AUTH: user said "go ahead"'))
        self.assertIsNone(gate_lines.find("AUTH", '- **AUTH: user said "go"**'))

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


class SettingsRetractionTests(unittest.TestCase):
    """A grant withdrawn from source must leave the deployed file.

    The merge is a union, which cannot tell a permission the machine accepted
    interactively from one this repo granted and has since removed. Without
    provenance the second kind is deployed forever — permissions only ever
    accumulate, which is the wrong direction for a permission.
    """

    SCRIPT = ROOT / "scripts/merge-settings.py"

    def _merge(self, temp: Path, repo: dict) -> list:
        src, dst = temp / "src.json", temp / "dst.json"
        src.write_text(json.dumps(repo), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), str(src), str(dst),
             "--managed", str(temp / "managed.json")],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.last_stdout = result.stdout
        return json.loads(dst.read_text(encoding="utf-8"))["permissions"]["allow"]

    def test_withdrawn_grant_is_retracted_and_foreign_entries_survive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            (temp / "dst.json").write_text(
                json.dumps({"permissions": {"allow": ["Bash(machine:*)"]}}),
                encoding="utf-8")
            self._merge(temp, {"permissions": {"allow": ["Bash(ls:*)",
                                                         "Bash(rm:*)"]}})
            allow = self._merge(temp, {"permissions": {"allow": ["Bash(ls:*)"]}})
            self.assertNotIn("Bash(rm:*)", allow)
            self.assertIn("Bash(machine:*)", allow)
            self.assertIn("retracted", self.last_stdout)

    def test_withdrawn_agent_registration_is_retracted_from_config(self) -> None:
        """Same defect at section level: a role dropped from source stayed registered."""
        script = ROOT / "scripts/merge-toml.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            src, dst, man = temp / "src.toml", temp / "dst.toml", temp / "m.json"
            dst.write_text('[model]\nname = "gpt"\n\n[agents.mine]\nconfig_file = "x"\n',
                           encoding="utf-8")

            def merge(repo: str) -> str:
                src.write_text(repo, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(script), str(src), str(dst),
                     "--managed", str(man)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.last_stdout = result.stdout
                return dst.read_text(encoding="utf-8")

            merge('[agents.verifier]\nconfig_file = "v"\n\n'
                  '[agents.executor]\nconfig_file = "e"\n')
            text = merge('[agents.verifier]\nconfig_file = "v"\n')
            self.assertNotIn("[agents.executor]", text)
            self.assertIn("retracted section", self.last_stdout)
            # The user's own agent and every machine section are untouched.
            self.assertIn("[agents.mine]", text)
            self.assertIn("[model]", text)

    def test_a_fresh_install_records_what_it_owns(self) -> None:
        """The install that writes the file also owns every entry in it.

        Both mergers used to write the target and return before touching the
        sidecar, so provenance began at the *second* sync. A missing sidecar
        means "unknown, keep everything", which made a v1 fresh install the one
        deployment whose entries could never be withdrawn: v2 read them back as
        machine state (2026-07-29). Every retraction test before this one
        pre-created the target, so none of them went through that branch.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            self._merge(temp, {"permissions": {"allow": ["Bash(ls:*)",
                                                         "Bash(rm:*)"]}})
            deployed = json.loads((temp / "dst.json").read_text(encoding="utf-8"))
            deployed["permissions"]["allow"].append("Bash(machine:*)")
            (temp / "dst.json").write_text(json.dumps(deployed), encoding="utf-8")

            allow = self._merge(temp, {"permissions": {"allow": ["Bash(ls:*)"]}})
            self.assertNotIn("Bash(rm:*)", allow)
            self.assertIn("Bash(machine:*)", allow)
            self.assertIn("Bash(ls:*)", allow)

        script = ROOT / "scripts/merge-toml.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            src, dst, man = temp / "src.toml", temp / "dst.toml", temp / "m.json"

            def merge(repo: str) -> str:
                src.write_text(repo, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(script), str(src), str(dst),
                     "--managed", str(man)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return dst.read_text(encoding="utf-8")

            merge('[agents.verifier]\nconfig_file = "v"\n\n'
                  '[agents.executor]\nconfig_file = "e"\n')
            dst.write_text(dst.read_text(encoding="utf-8")
                           + '\n[agents.mine]\nconfig_file = "x"\n',
                           encoding="utf-8")
            text = merge('[agents.verifier]\nconfig_file = "v"\n')
            self.assertNotIn("[agents.executor]", text)
            self.assertIn("[agents.mine]", text)
            self.assertIn("[agents.verifier]", text)

    def test_entries_of_unknown_provenance_are_never_deleted(self) -> None:
        """An upgrade has no sidecar yet; unknown must not mean machine-owned."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            (temp / "dst.json").write_text(
                json.dumps({"permissions": {"allow": ["Bash(ls:*)",
                                                      "Bash(legacy:*)"]}}),
                encoding="utf-8")
            allow = self._merge(temp, {"permissions": {"allow": ["Bash(ls:*)"]}})
            self.assertIn("Bash(legacy:*)", allow)


class VerifierQuotaTests(unittest.TestCase):
    """One outcome verifier per top-level task, refused rather than recommended.

    The rule sat in four files as prose with nothing able to enforce it, and
    the second verifier always feels justified at the time — which is why the
    budget has to be spent by a mechanism.
    """

    HOOK = ROOT / "main/claude/hooks/verifier-quota.py"

    def _dispatch(self, home: Path, subagent: str = "verifier",
                  prompt: str | None = "p1", **env) -> int:
        payload = {"tool_name": "Agent", "session_id": "s1",
                   "tool_input": {"subagent_type": subagent}}
        if prompt is not None:
            payload["prompt_id"] = prompt
        return subprocess.run(
            [sys.executable, str(self.HOOK)], input=json.dumps(payload),
            capture_output=True, text=True,
            env={**os.environ, "HOME": str(home), **env}).returncode

    def test_the_second_verifier_in_one_prompt_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(self._dispatch(Path(home)), 0)
            self.assertEqual(self._dispatch(Path(home)), 2)
            # A new prompt gets a new quota. This is the enforcement gap, not
            # the enforcement: a task continued in the next prompt is the same
            # task under the contract's rule, and no payload field says so. The
            # gate under-enforces here on purpose (keying on the session would
            # refuse every later task's legitimate verifier), so the scope has
            # to be stated as "prompt" everywhere it is described.
            self.assertEqual(self._dispatch(Path(home), prompt="p2"), 0)

    def test_nothing_describes_the_gate_as_enforcing_per_task(self) -> None:
        """The disclosure is the fix, so the disclosure is load-bearing.

        A reader who believes the hook is per-task trusts it in exactly the
        case it does not cover. Until a stable task id reaches the payload,
        every place that describes the *mechanism* says prompt; the contracts
        keep saying task because that is the judgment rule the gate backs up.

        Asserting the honest sentences exists is not enough on its own: three
        of them were in place while `README.md` and `docs/architecture.md`
        still said the mechanism blocks the second verifier of a task
        (2026-07-29 review). So the second half sweeps instead of sampling —
        wherever a passage pairs the interception with task scope, it has to
        name the prompt boundary in the same breath.
        """
        scoped = {
            "main/claude/hooks/verifier-quota.py": "per user prompt",
            "README.md": "同一個 prompt 內的第二個",
            "docs/hook-system.md": "以 prompt 為界",
            "docs/dispatch-lifecycle.md": "托底的單位是",
        }
        for path, disclosure in scoped.items():
            self.assertIn(disclosure, read(path), path)
        for contract in ("main/claude/CLAUDE.contract.md",
                         "main/codex/AGENTS.contract.md"):
            self.assertIn("per top-level task", read(contract), contract)

        # The contracts are exempt by construction: they state the rule, whose
        # unit really is the task. Everything below describes the machine.
        described = ["README.md", "main/claude/hooks/verifier-quota.py"]
        described += [f"docs/{doc.name}" for doc in sorted((ROOT / "docs").glob("*.md"))]
        blocking = ("攔截", "攔得住", "擋", "blocked", "blocks")
        for path in described:
            for passage in re.split(r"\n\s*\n", read(path)):
                if "verifier" not in passage or "task" not in passage:
                    continue
                if not any(word in passage for word in blocking):
                    continue
                self.assertIn(
                    "prompt", passage,
                    f"{path}: describes the verifier gate intercepting per task "
                    "without naming the prompt boundary it actually keys on:\n"
                    f"{passage}")

    def test_only_the_outcome_verifier_spends_the_quota(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            for role in ("plan-verifier", "security-reviewer", "executor"):
                self.assertEqual(self._dispatch(Path(home), subagent=role), 0, role)
            self.assertEqual(self._dispatch(Path(home)), 0)

    def test_an_explicit_override_lets_a_real_new_task_through(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(self._dispatch(Path(home)), 0)
            self.assertEqual(
                self._dispatch(Path(home), AGENT_ALLOW_SECOND_VERIFIER="1"), 0)

    def test_a_missing_carrier_does_not_block_the_dispatch(self) -> None:
        """A budget guard, unlike a safety boundary, may not refuse blind."""
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(self._dispatch(Path(home), prompt=None), 0)
            self.assertEqual(self._dispatch(Path(home), prompt=None), 0)

    def test_unwritable_state_fails_open_and_the_docs_say_so(self) -> None:
        """The one gate that is fail-closed on condition and fail-open on itself.

        Every other entry in the fail-closed table also refuses when its own
        machinery breaks - an unrunnable suite, an unreadable version, an
        unresolvable target all block. This one does not: `load()` reads an
        unwritable state directory as an empty budget and `save()` swallows the
        error, so two verifiers in one prompt both proceed. That is the
        deliberate design (it is a budget guard, not a safety boundary), but
        the docs classified it purely by `return 2` and therefore promised a
        posture it does not have (2026-08-03 review).

        Asserted behaviourally *and* against the prose, because the source-
        derived gate count in `test_deployment.py` cannot see the difference.
        """
        with tempfile.TemporaryDirectory() as home:
            state = Path(home) / ".claude" / "telemetry"
            state.mkdir(parents=True)
            state.chmod(0o500)
            try:
                self.assertEqual(self._dispatch(Path(home)), 0)
                self.assertEqual(
                    self._dispatch(Path(home)), 0,
                    "state failure now blocks; the docs below must change with it")
            finally:
                state.chmod(0o700)
            # Control: the same two dispatches against writable state.
            self.assertEqual(self._dispatch(Path(home)), 0)
            self.assertEqual(self._dispatch(Path(home)), 2)

        doc = read_repo("docs/hook-system.md")
        row = next(line for line in doc.splitlines()
                   if line.startswith("| [verifier-quota]"))
        self.assertIn("狀態健康", row,
                      "the fail-closed table does not disclose that this gate "
                      "fails open on its own state failure")

    def test_a_carrier_that_stopped_arriving_becomes_a_standing_finding(self) -> None:
        """Silent retirement is the failure mode of an unread budget guard.

        The gate reads one optional payload field. If a CLI change stops
        sending it, every dispatch is allowed with a note on a stderr nobody
        re-reads, and the tests still pass because they supply the field
        themselves. The count is what makes the loss observable; it clears on
        the first dispatch that does carry the field, so it cannot become an
        alarm nobody can turn off.
        """
        state = "/.claude/telemetry/.verifier-quota.json"

        def misses(home: Path) -> object:
            return (json.loads((Path(str(home) + state)).read_text(
                encoding="utf-8")).get("_carrier") or {}).get("misses")

        with tempfile.TemporaryDirectory() as home:
            for expected in (1, 2, 3):
                self.assertEqual(self._dispatch(Path(home), prompt=None), 0)
                self.assertEqual(misses(Path(home)), expected)

            hook = ROOT / "main/claude/hooks/weekly-integrity.py"
            env = {**os.environ, "HOME": home,
                   "AGENT_HARNESS_REPO": str(Path(home) / "repo")}
            report = subprocess.run([sys.executable, str(hook)], env=env,
                                    check=True, capture_output=True, text=True)
            self.assertIn("verifier quota not enforceable", report.stdout)
            self.assertIn("prompt_id", report.stdout)

            # A dispatch that carries the field says the gate works again.
            self.assertEqual(self._dispatch(Path(home)), 0)
            self.assertIsNone(misses(Path(home)))

    def test_two_verifiers_dispatched_at_once_still_spend_one_quota(self) -> None:
        """The parallel case is the one the gate exists for.

        This harness batches dispatches into a single assistant message, so the
        two verifiers worth refusing arrive together rather than in sequence.
        An unlocked read-check-write lets both read an unspent quota and both
        proceed — the gate passes every sequential test and refuses nothing in
        the situation it was written for.
        """
        import time
        payload = json.dumps({"tool_name": "Agent", "session_id": "s1",
                              "prompt_id": "p1",
                              "tool_input": {"subagent_type": "verifier"}})
        with tempfile.TemporaryDirectory() as home:
            # Spawn every hook first, feed them second. The hook blocks on
            # stdin, so closing all the pipes together releases eight already
            # warm interpreters into the check-and-set at once. Spawning them
            # and letting each run to completion measures nothing: interpreter
            # start-up alone staggers them enough that an unlocked hook passes
            # (checked 2026-07-29 — that version of this test could not tell
            # the lock from its absence).
            running = [
                subprocess.Popen(
                    [sys.executable, str(self.HOOK)], text=True,
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env={**os.environ, "HOME": home})
                for _ in range(8)
            ]
            for process in running:
                process.stdin.write(payload)
            time.sleep(0.5)
            for process in running:
                process.stdin.close()
            codes = [process.wait(timeout=60) for process in running]
        self.assertEqual(sorted(codes), [0] + [2] * 7, codes)


class BridgeJobLivenessTests(unittest.TestCase):
    """A dead launcher is not a dead dispatch.

    Reconstructs the 2026-07-26 duplicate: a forwarder hit the two-minute Bash
    cap, relaunched the same prompt, and both Codex jobs stayed live against
    one workspace. The check has to see two, because the wrong answer here is
    two agents owning the same artifacts.
    """

    SCRIPT = ROOT / "main/codex/scripts/bridge-jobs"

    def _state(self, temp: Path, jobs: list[dict]) -> dict:
        job_dir = temp / "workspace-hash" / "jobs"
        job_dir.mkdir(parents=True)
        for job in jobs:
            (job_dir / f"{job['id']}.json").write_text(
                json.dumps(job), encoding="utf-8")
        return {**os.environ, "CODEX_COMPANION_STATE": str(temp)}

    @staticmethod
    def _job(job_id: str, *, status: str = "running", summary: str = "review",
             session: str = "s1", started: str = "2026-07-26T00:00:00Z",
             pid: int | None = None) -> dict:
        return {"id": job_id, "status": status, "phase": status,
                "summary": summary, "sessionId": session, "write": False,
                "workspaceRoot": "/w", "startedAt": started,
                "pid": os.getpid() if pid is None else pid}

    def _run(self, env: dict, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(self.SCRIPT), *args],
                              env=env, capture_output=True, text=True)

    def test_twin_jobs_from_one_relaunched_prompt_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = self._state(Path(temp_dir), [
                self._job("task-a", started="2026-07-26T00:00:00Z"),
                self._job("task-b", started="2026-07-26T00:02:48Z"),
            ])
            result = self._run(env, "--duplicates")
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("duplicate dispatch", result.stdout)
            for job_id in ("task-a", "task-b"):
                self.assertIn(f"/codex:cancel {job_id}", result.stdout)

    def test_state_is_found_without_being_told_where_it_is(self) -> None:
        """The default path has to work, because that is the one operators use.

        Every other test here sets `CODEX_COMPANION_STATE`, so all of them
        passed while the shipped default pointed at an empty
        `codex-openai-codex/state` and the companion wrote to
        `codex-inline/state`. Result: exit 2 on every real run, and the
        duplicate reconciliation the dispatch contract requires before a
        relaunch never actually answered (observed 2026-07-30).

        A plugin data directory is `<plugin>-<marketplace>` and the marketplace
        half is the user's install choice, so the fixture uses a name this repo
        has never heard of. Nothing may be passed in but HOME.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            state = home / ".claude/plugins/data/codex-somewhere-else/state"
            jobs = state / "workspace-hash" / "jobs"
            jobs.mkdir(parents=True)
            for job_id in ("task-a", "task-b"):
                (jobs / f"{job_id}.json").write_text(
                    json.dumps(self._job(job_id)), encoding="utf-8")
            env = {**os.environ, "HOME": str(home)}
            env.pop("CODEX_COMPANION_STATE", None)

            result = self._run(env, "--duplicates")
            self.assertEqual(result.returncode, 1,
                             result.stdout + result.stderr)
            self.assertIn("duplicate dispatch", result.stdout)

        # An absent root still reports "unknown", never "nothing running".
        with tempfile.TemporaryDirectory() as empty:
            env = {**os.environ, "HOME": empty}
            env.pop("CODEX_COMPANION_STATE", None)
            blind = self._run(env, "--duplicates")
            self.assertEqual(blind.returncode, 2, blind.stdout)
            self.assertIn("not the same as no jobs running", blind.stderr)

    def test_genuinely_parallel_dispatches_are_not_twins(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = self._state(Path(temp_dir), [
                self._job("task-a", summary="review contracts"),
                self._job("task-b", summary="review routing"),
            ])
            result = self._run(env, "--duplicates")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no duplicate", result.stdout)

    def test_finished_jobs_never_count_as_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = self._state(Path(temp_dir), [
                self._job("task-a"),
                self._job("task-b", status="cancelled"),
                self._job("task-c", status="completed"),
            ])
            result = self._run(env, "--duplicates")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("1 live", result.stdout)

    def test_a_job_whose_process_died_is_not_live(self) -> None:
        """`status: running` outlives the process that earned it.

        The 2026-07-26 review job died and its state file never noticed; a
        guard that trusts the status field would have reported a phantom
        writer forever, and its twin check would key off a job that is gone.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            env = self._state(Path(temp_dir), [
                self._job("task-dead", pid=2 ** 22),
                self._job("task-live"),
            ])
            result = self._run(env, "--duplicates")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("1 live", result.stdout)
            self.assertIn("died without updating their state", result.stdout)
            self.assertIn("task-dead", result.stdout.split(
                "died without updating their state")[1])

    def test_an_uncheckable_pid_still_counts_as_live(self) -> None:
        """Over-reporting is the safe direction for a duplicate guard."""
        with tempfile.TemporaryDirectory() as temp_dir:
            job = self._job("task-a")
            job.pop("pid")
            env = self._state(Path(temp_dir), [job, self._job("task-b")])
            result = self._run(env, "--duplicates")
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("duplicate dispatch", result.stdout)

    def test_missing_state_refuses_to_answer_instead_of_clearing(self) -> None:
        env = {**os.environ, "CODEX_COMPANION_STATE": "/nonexistent-state"}
        result = self._run(env, "--duplicates")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("not the same as no jobs running", result.stderr)
        self.assertNotIn("no duplicate", result.stdout)


class DenialLogTests(unittest.TestCase):
    """Denials were the one thing the gates do that nothing recorded, so
    answering "how often does this fire" meant grepping transcripts - and the
    hooks' own docstrings contain the block strings, which is how the first
    three attempts at that question came back wrong. These assert the two
    properties that make the log worth having: it records, and it cannot break
    the gate it observes."""

    def _deny(self, home: Path, extra_env: dict | None = None):
        hook = ROOT / "main/claude/hooks/leaf-redispatch.py"
        env = {**os.environ, "HOME": str(home), **(extra_env or {})}
        return subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps({"tool_name": "Agent", "agent_type": "executor",
                              "session_id": "sess-test"}),
            capture_output=True, text=True, env=env)

    def test_a_denial_is_recorded_with_enough_to_count_it(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self._deny(Path(home))
            self.assertEqual(result.returncode, 2, result.stderr)
            log = Path(home) / ".claude" / "telemetry" / "denials.jsonl"
            self.assertTrue(log.exists(), "denial produced no row")
            row = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
            # A reason code rather than prose: counting runs of denials must not
            # depend on parsing the message a human reads.
            self.assertEqual(row["gate"], "leaf-redispatch")
            self.assertEqual(row["reason"], "leaf-tried-to-dispatch")
            self.assertEqual(row["session_id"], "sess-test")
            self.assertIn("ts", row)

    def test_an_unwritable_log_still_blocks(self) -> None:
        """The gate is fail-closed on its condition and fail-open on its
        bookkeeping. If those ever swap, a broken telemetry directory turns
        into a boundary that silently stops holding."""
        with tempfile.TemporaryDirectory() as home:
            # Occupy the telemetry path with a file so makedirs cannot create it.
            claude = Path(home) / ".claude"
            claude.mkdir()
            (claude / "telemetry").write_text("not a directory", encoding="utf-8")
            result = self._deny(Path(home))
            self.assertEqual(result.returncode, 2,
                             "logging failure must not turn a block into a pass")
            self.assertIn("[leaf-redispatch] blocked", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_the_module_is_deployed_next_to_the_hooks_that_import_it(self) -> None:
        # The hooks import it as a sibling, so it has to travel with them; the
        # manifest ships the directory, and this catches a future move out of it.
        self.assertTrue((ROOT / "main/claude/hooks/denial_log.py").exists())
        for hook in ("leaf-redispatch.py", "runtime-guard.py",
                     "verifier-quota.py", "commit-test-gate.py"):
            source = (ROOT / "main/claude/hooks" / hook).read_text(encoding="utf-8")
            with self.subTest(hook=hook):
                self.assertIn("import denial_log", source)
                self.assertIn("denial_log = None", source,
                              f"{hook}: import must fall back, not raise")


class TrapSurfaceTests(unittest.TestCase):
    """The surface declaration is what dates a trap's evidence, so it is the one
    part of the mechanism that has to be checked rather than reported. A surface
    listing a path that no longer exists produces a fingerprint over the wrong
    set of bytes, and the result rows it stamps would claim to be current while
    measuring something else. That is a determinate error, unlike a stale stamp,
    which is usually just the rules having improved."""

    def _traps(self) -> list[Path]:
        # `evals/replay/` measures behaviour too and sits one level shallower
        # than the traps, so it declares a surface for the same reason and is
        # checked by the same tests.
        return sorted(set((ROOT / "evals" / "traps").glob("*/"))
                      | {listing.parent
                         for listing in ROOT.glob("evals/*/surface.tsv")})

    def test_every_trap_declares_the_surface_its_results_depend_on(self) -> None:
        for trap in self._traps():
            with self.subTest(trap=trap.name):
                self.assertTrue(
                    (trap / "surface.tsv").exists(),
                    f"{trap.name}: no surface.tsv, so its result rows cannot say "
                    "which bytes produced them")

    def test_every_declared_surface_path_exists(self) -> None:
        for trap in self._traps():
            listing = trap / "surface.tsv"
            if not listing.exists():
                continue
            for raw in listing.read_text(encoding="utf-8").splitlines():
                path = raw.strip()
                if not path or path.startswith("#"):
                    continue
                with self.subTest(trap=trap.name, path=path):
                    self.assertTrue(
                        (ROOT / path).exists(),
                        f"{trap.name}: surface lists {path}, which is gone; the "
                        "fingerprint would silently cover a different set")

    def test_the_fingerprint_is_deterministic_and_covers_every_listed_file(self) -> None:
        module = load_module(
            "trap_surface", ROOT / "evals" / "scripts" / "trap-surface.py")
        for trap in self._traps():
            if not (trap / "surface.tsv").exists():
                continue
            with self.subTest(trap=trap.name):
                first, members = module.fingerprint(trap.name)
                second, _ = module.fingerprint(trap.name)
                self.assertEqual(first, second, "fingerprint is not stable")
                self.assertEqual(
                    [member["path"] for member in members],
                    module.surface_paths(trap.name),
                    "fingerprint skipped a declared file")

    def test_the_selection_surface_lists_every_skill_the_bundle_is_built_from(self) -> None:
        """The two tests above check the list's members. Neither checks the list.

        `s10-skill-recall` shows the difference and cost it on 2026-08-17. Its
        `surface.tsv` was hand-kept while `build.py` renders the bundle by
        globbing `main/claude/skills/*/SKILL.md`, so installing two skills put
        eight descriptions in front of the agent under test and left the
        fingerprint covering six. Every existing check stayed green:
        `test_every_declared_surface_path_exists` verifies that what is listed is
        there, and `build.py --check` verifies the bundle matches the live
        frontmatters — nothing compared the surface against the generator.

        The consequence is worse than a stale fingerprint. A stamp taken in that
        state reads as current, so the one mechanism that dates this trap's
        evidence would have been actively wrong rather than merely absent.
        """
        build = load_module(
            "s10_build", ROOT / "evals/traps/s10-skill-recall/build.py")
        rendered_from = {
            str(path.relative_to(ROOT))
            for path in sorted(build.SKILLS.iterdir())
            if (path / "SKILL.md").is_file()
            for path in [path / "SKILL.md"]}
        module = load_module(
            "trap_surface", ROOT / "evals" / "scripts" / "trap-surface.py")
        declared = set(module.surface_paths("s10-skill-recall"))
        self.assertEqual(
            set(), rendered_from - declared,
            "the bundle is built from a skill this trap's surface does not "
            "fingerprint, so its stamps would claim to cover a choice they omit")

    # Dated result rows carrying no surface stamp, per trap, measured
    # 2026-08-17. These are frozen, not approved: they can be lowered by
    # stamping a row, and a new unstamped row anywhere fails.
    UNSTAMPED_ROW_CEILING = {
        "replay": 0,
        "s7-false-completion": 17,
        "s8-spec-conflict": 8,
        "s9-tz-bucketing": 7,
        "s10-skill-recall": 12,
        "s11-pointer-redundancy": 0,
    }

    def test_no_trap_gains_a_result_row_that_cannot_be_dated(self) -> None:
        """`evidence-check` counts unstamped rows and always exits 0; this holds the line.

        Reporting was the right call for that script - made fail-closed, the
        cheapest way to stay green is to stop writing the date beside what was
        checked. But a number that only ever gets printed is a number that grows,
        and s10 showed the bill. Installing a fifth shared skill regenerated its
        option bundle, correctly and with `build.py --check` guarding every
        future run; the twelve rows already written carry no stamp, so they now
        describe a measurement on a set of options that no longer exists, and
        nothing in the artifact says so.

        Those twelve cannot be stamped after the fact, which is exactly why the
        ceiling is per trap rather than a total: a trap deleting rows must not
        buy another trap room to add unstamped ones. The direction that stays
        green is stamping.
        """
        module = load_module("evidence_check", ROOT / "scripts" / "evidence-check.py")
        counted = {row["trap"]: row for row in module.audit_traps()}
        self.assertEqual(
            sorted(counted), sorted(self.UNSTAMPED_ROW_CEILING),
            "a trap appeared or vanished; give it a ceiling of 0 and stamp its rows")
        for trap, ceiling in sorted(self.UNSTAMPED_ROW_CEILING.items()):
            with self.subTest(trap=trap):
                self.assertLessEqual(
                    counted[trap]["unstamped_rows"], ceiling,
                    f"{trap}: a dated result row carries no surface fingerprint, so "
                    "it cannot say which bytes produced it. Stamp the new row "
                    "rather than raising this number")


class UntiedDispatchIdTests(unittest.TestCase):
    """The weekly half of the same check `experience-log` now makes at write
    time. It has to fire on the two shapes that actually happened and stay
    quiet on every id a hook or `experience-stage` produces, because both of
    those build `<session>:<agent>` and a detector that flagged them would be
    reporting normal operation."""

    def _pattern(self):
        """Read the pattern out of the source without running the hook.

        `weekly-integrity.py` is a top-level script: importing it runs every
        check and exits. Restructuring a deployed hook to make one regex
        importable is not worth it, and copying the literal into the test would
        let the two drift. Parsing the assignment tracks whatever the hook
        actually uses."""
        import ast
        import re as regex

        source = (ROOT / "main/claude/hooks/weekly-integrity.py").read_text(
            encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if (isinstance(node, ast.Assign)
                    and any(getattr(t, "id", None) == "UNTIED_ID"
                            for t in node.targets)):
                return regex.compile(ast.literal_eval(node.value.args[0]))
        self.fail("weekly-integrity.py no longer defines UNTIED_ID")

    def test_it_accepts_every_id_a_carrier_actually_stages(self) -> None:
        pattern = self._pattern()
        for good in (
            "3fcb0933-1e15-4036-a951-52945b395d0a:a4fc118c83bfa42ed",  # hook
            "b73317aa-9fff-4f7a-84f4-d48c193f1965:a046384e7",          # stage
            "62D8C5A2-8BA9-44A3-9B24-A6CF3C19EB5D:aBcD1234",           # upper
        ):
            with self.subTest(id=good):
                self.assertIsNotNone(pattern.match(good))

    def test_it_flags_the_two_shapes_that_reconciled_nothing(self) -> None:
        pattern = self._pattern()
        for bad in (
            "a4fc118c83bfa42ed",   # agent id without its session prefix
            "rv-policy-01",        # invented label
            "s8a1",                # the operator's own, 2026-08-10
            "",
        ):
            with self.subTest(id=bad):
                self.assertIsNone(pattern.match(bad))


class ReplayScenarioTests(unittest.TestCase):
    """Criterion 2 says a reach marker only counts if it was written before the
    run, and that a marker keyed on something the fixture does not uniquely
    contain lets a derailed run pass. Both properties are checkable, so they are
    checked here rather than trusted.

    The `DECISION:` matcher gets its own negative control for a specific reason:
    the first draft anchored on a bare line start, scored the 2026-08-12 r2
    pilot 0 of 5, and was wrong — four of those five turns had emitted the
    marker decorated as ``**`DECISION:` …**``. An instrument that manufactures
    the lapse it detects is worse than no instrument, and this is the second
    time in this repo that a checker keyed on rendering rather than substance
    produced a false finding (s8's `a19` was the first)."""

    REPLAY = ROOT / "evals" / "replay"
    # The repo's copy, never `~/.claude/CLAUDE.md`. The probe builders read a
    # contract to decide which way their two-sided check points, and a test that
    # let them read the deployed file would pass or fail on what the operator
    # happened to have installed that afternoon.
    CONTRACT = ROOT / "main" / "claude" / "CLAUDE.contract.md"

    def _grader(self):
        return load_module("replay_grade", self.REPLAY / "grade.py")

    def _scenarios(self) -> list[Path]:
        return sorted((self.REPLAY / "scenarios").glob("*.md"))

    def test_the_scenario_index_is_generated_and_current(self) -> None:
        """A directory listing of opaque prefixes is unreadable, and the fix
        must not be a table maintained by hand.

        `e4` exists because a condition typed beside the artifact that already
        states it diverges, so the index is rendered from each scenario's own
        frontmatter and this asserts the rendered block is what the README
        holds. A new scenario without a row is red, not merely undocumented,
        and the row cannot disagree with what a run is graded against.
        """
        index = subprocess.run(
            [sys.executable, str(self.REPLAY / "scenario-index.py"), "--check"],
            capture_output=True, text=True)
        self.assertEqual(index.returncode, 0,
                         index.stderr or index.stdout)

    def test_every_trap_appears_in_the_trap_index(self) -> None:
        """The traps carry no frontmatter, so their index is written by hand —
        which is exactly the shape that drifts. This pins both directions."""
        traps = ROOT / "evals" / "traps"
        listed = {path.name for path in traps.iterdir()
                  if path.is_dir() and path.name != "__pycache__"}
        index = (traps / "README.md").read_text(encoding="utf-8")
        for name in sorted(listed):
            handle = name.split("-")[0]
            with self.subTest(trap=name):
                self.assertIn(f"| `{handle}` |", index,
                              f"{name}: no row in evals/traps/README.md")
                self.assertIn(f"{name}/README.md", index,
                              f"{name}: index row does not link to it")
        # And nothing in the index that no longer exists on disk.
        for handle in re.findall(r"^\| `(s\d+)` \|", index, re.M):
            with self.subTest(row=handle):
                self.assertTrue(
                    any(name.startswith(f"{handle}-") for name in listed),
                    f"{handle}: index row for a trap that is gone")

    def test_every_scenario_pre_declares_marker_and_recovery_point(self) -> None:
        module = load_module("replay_run", self.REPLAY / "run.py")
        for scenario in self._scenarios():
            with self.subTest(scenario=scenario.name):
                spec, turns = module.parse_scenario(scenario)
                for field in ("id", "fixture", "marker", "recovery_point",
                              "expect"):
                    self.assertTrue(spec.get(field),
                                    f"{scenario.name}: {field} is empty")
                self.assertTrue(turns, "a scenario needs at least one turn")

    def test_marker_tokens_are_absent_from_the_prompts_the_agent_sees(self) -> None:
        # s11, 2026-08-08: five of six scenarios named files that did not
        # exist, and the marker still matched because the agent echoed the
        # filename back while reporting it missing. A token the prompt contains
        # is not evidence the run opened anything.
        build = load_module("replay_build", self.REPLAY / "fixtures" / "build.py")
        tokens = [build.token(scope, index)
                  for scope in ("qz7", "K41", "V7", "bk", "K90", "V3")
                  for index in range(0, 13)]
        for scenario in self._scenarios():
            body = scenario.read_text(encoding="utf-8")
            for value in tokens:
                with self.subTest(scenario=scenario.name, token=value):
                    self.assertNotIn(value, body)

    def test_fixtures_are_byte_identical_across_builds(self) -> None:
        import hashlib

        build = load_module("replay_build", self.REPLAY / "fixtures" / "build.py")
        for name in sorted(build.BUILDERS):
            with self.subTest(fixture=name), tempfile.TemporaryDirectory() as a, \
                    tempfile.TemporaryDirectory() as b:
                digests = []
                for root in (Path(a), Path(b)):
                    build.build(name, root)
                    stamp = hashlib.sha256()
                    for path in sorted(root.rglob("*")):
                        if path.is_file():
                            stamp.update(str(path.relative_to(root)).encode())
                            stamp.update(path.read_bytes())
                    digests.append(stamp.hexdigest())
                self.assertEqual(digests[0], digests[1])

    def test_the_decision_matcher_fires_on_the_forms_a_run_actually_used(self) -> None:
        pattern = self._grader().DECISION_LINE
        for line in (
            "2. **`DECISION:` 邊界語意統一成 `>=`。** 原本最高級距用的是嚴格大於",
            "**`DECISION:` 進位方式選 ROUND_HALF_UP**",
            "DECISION: cap applied after rounding, because the table is in cents",
            "- DECISION: raise on negative input",
            "  > **DECISION**: clamp to zero",
        ):
            with self.subTest(line=line[:40]):
                self.assertTrue(pattern.search(line))

    def test_the_fault_detector_reads_the_run_and_not_the_documents_it_read(self) -> None:
        # Second misfire of the same shape, same afternoon: a first draft also
        # matched the bare words `Overloaded` and `rate limit`, and reported a
        # provider fault in a healthy run because the agent had read a skill
        # reference containing the phrase. Tool results carry arbitrary
        # document text; a detector looser than the provider's own signature
        # measures the corpus.
        module = self._grader()
        real = ("Agent terminated early due to an API error: API Error: 529 "
                "Overloaded. This is a server-side issue, usually temporary")
        self.assertEqual("529", module.API_FAULT.search(real).group(1))
        self.assertTrue(module.API_FAULT_GENERIC.search(real))
        for prose in (
            "Use only after delegation passes the dispatch brake; rate limits "
            "are covered in references/metrics.md",
            "The gateway was overloaded, which is why the runbook asks for 5.",
        ):
            with self.subTest(prose=prose[:40]):
                self.assertIsNone(module.API_FAULT.search(prose))
                self.assertIsNone(module.API_FAULT_GENERIC.search(prose))

    def test_the_arm_swap_restores_the_contract_including_after_a_crash(self) -> None:
        """The one piece of this suite that writes to a live user contract.

        Exercised against injected paths, never the real ones: a test that
        proves the restore works by swapping the operator's own contract is a
        test that can leave the machine broken exactly when it fails."""
        module = load_module("replay_arm", self.REPLAY / "arm.py")
        source = ROOT / "main" / "claude" / "CLAUDE.contract.md"
        original = source.read_text(encoding="utf-8")

        for arm, crash in (("b", False), ("c", False), ("b", True)):
            with self.subTest(arm=arm, crash=crash), \
                    tempfile.TemporaryDirectory() as temp:
                home = Path(temp)
                deployed = home / "CLAUDE.md"
                deployed.write_text(original, encoding="utf-8")
                paths = module.Paths(deployed=deployed, source=source,
                                     sentinel=home / ".sentinel")
                before = module.sha(deployed)

                def run() -> dict:
                    with module.contract_arm("baton-dispatch", arm, paths) as state:
                        self.assertTrue(paths.sentinel.exists(),
                                        "no breadcrumb while swapped")
                        self.assertNotEqual(
                            before, module.sha(deployed),
                            f"arm {arm} did not change the contract")
                        if crash:
                            raise RuntimeError("simulated crash mid-run")
                        return state

                if crash:
                    with self.assertRaises(RuntimeError):
                        run()
                else:
                    state = run()
                    self.assertEqual(
                        0 if arm == "c" else 1,
                        state["clause_name_mentions_in_effect"],
                        "arm C must leave no mention; arm B keeps the name")

                self.assertEqual(before, module.sha(deployed),
                                 "contract not restored")
                self.assertFalse(paths.sentinel.exists(),
                                 "sentinel survived a verified restore")

    def test_the_reverse_control_clause_is_removable_from_the_real_contract(self) -> None:
        # The whole point of a reverse control is that it is the one arm
        # expected to show an effect, so an arm that silently failed to apply
        # would be the worst possible failure here: it would look like the
        # instrument is blind. `variant` refuses a literal that is not present
        # exactly once, and this checks that refusal never has to fire.
        arms = load_module(
            "s11_arms",
            self.REPLAY.parent / "traps" / "s11-pointer-redundancy" / "arms.py")
        shipped = (self.REPLAY.parents[1] / "main" / "claude"
                   / "CLAUDE.contract.md").read_text(encoding="utf-8")
        stripped = arms.variant(shipped, "language", "b")
        self.assertLess(len(stripped), len(shipped))
        self.assertIn("Traditional Chinese", shipped)
        self.assertNotIn("Traditional Chinese", stripped)
        self.assertEqual(arms.variant(shipped, "language", "c"), stripped,
                         "the clause names no skill, so B and C coincide")

    def test_the_manipulation_check_asks_something_that_can_fail(self) -> None:
        # Asking whether a skill is named is the right question for a pointer
        # and the wrong one for a rule that names none: `language` would answer
        # NO in both arms, and a probe that cannot fail is not a probe.
        arms = load_module(
            "s11_arms",
            self.REPLAY.parent / "traps" / "s11-pointer-redundancy" / "arms.py")
        pointer = arms.probe("baton-dispatch")
        self.assertIn("baton-dispatch", pointer)
        self.assertIn("skill", pointer)
        language = arms.probe("language")
        self.assertNotIn("skill", language)
        self.assertIn("language", language.lower())

    def _summariser(self):
        return load_module("replay_summarise", self.REPLAY / "summarise.py")

    def test_the_reverse_control_keeps_the_count_not_only_the_verdict(self) -> None:
        # The threshold that turns 84 Han characters into `in_chinese: True`
        # discards exactly what a sensitivity question needs: a clause weakened
        # until it halves the Chinese in a reply still scores 5 of 5 on the
        # binary and is invisible, while the counts separate cleanly. If the
        # count ever stops being reported, the next experiment runs on a ruler
        # this one deliberately un-blunted.
        module = self._grader()
        reply = "這個函式回傳費率乘上金額。" * 4 + " See `fee()` in pricing.py."
        with tempfile.TemporaryDirectory() as temp:
            outcome = module.grade_x1(
                Path(temp), {"id": "x1-language-floor"},
                {1: [{"type": "result", "result": reply}]})
        self.assertGreater(outcome["han_characters"], 20)
        self.assertGreater(outcome["latin_letters"], 0)
        self.assertTrue(outcome["in_chinese"])

    def test_one_quoted_term_does_not_count_as_a_chinese_reply(self) -> None:
        module = self._grader()
        with tempfile.TemporaryDirectory() as temp:
            outcome = module.grade_x1(
                Path(temp), {"id": "x1-language-floor"},
                {1: [{"type": "result",
                      "result": "It returns the fee, i.e. the 費率 times the "
                                "amount in cents."}]})
        self.assertFalse(outcome["in_chinese"])
        self.assertEqual(2, outcome["han_characters"])

    def test_rank_separation_needs_the_ranges_to_come_apart(self) -> None:
        # At n=5 per arm, complete separation is the only shape that reaches
        # p < 0.05. A summary that reported the p-value alone would be asking a
        # reader to trust arithmetic they cannot check against the numbers on
        # the line above, so both are produced and both are checked here.
        module = self._summariser()
        shipped = [85, 80, 83, 88, 86]
        for label, other, disjoint, significant in (
            ("removed", [0, 0, 0, 0, 0], True, True),
            ("dose 0.9", [76, 72, 75, 79, 77], True, True),
            ("dose 0.95", [81, 76, 79, 84, 82], False, False),
        ):
            with self.subTest(case=label):
                result = module.rank_separation(shipped, other)
                self.assertTrue(result["comparable"])
                self.assertEqual(disjoint, result["ranges_disjoint"])
                self.assertEqual(significant, result["p_two_sided"] < 0.05)

    def test_rank_separation_refuses_instead_of_approximating(self) -> None:
        module = self._summariser()
        refused = module.rank_separation(list(range(15)), list(range(15)))
        self.assertFalse(refused["comparable"])
        self.assertIn("20", refused["why"])
        self.assertFalse(module.rank_separation([1, 2], [])["comparable"])

    def test_the_sandboxed_interpreter_refuses_rather_than_running_unconfined(self) -> None:
        # Fail closed is the whole design. A shim that silently stopped
        # confining would be worse than no shim, because `commands_run` would
        # still record a command that looks sandboxed.
        shim = self.REPLAY / "sandbox" / "python3"
        self.assertTrue(shim.exists() and os.access(shim, os.X_OK))
        env = {k: v for k, v in os.environ.items() if k != "REPLAY_WORKDIR"}
        done = subprocess.run([str(shim), "-c", "print('UNCONFINED')"],
                              capture_output=True, text=True, timeout=60, env=env)
        self.assertNotEqual(0, done.returncode)
        self.assertNotIn("UNCONFINED", done.stdout)
        self.assertIn("REPLAY_WORKDIR", done.stderr)

    def test_the_sandboxed_interpreter_writes_only_inside_the_workdir(self) -> None:
        # Measured 2026-08-17: a bare `Bash(python3:*)` grant let a session
        # write outside its workdir in 3 probes of 3. No permission string
        # fixes that, so this asserts the containment that does.
        shim = self.REPLAY / "sandbox" / "python3"
        if not Path("/usr/bin/sandbox-exec").exists():
            self.skipTest("sandbox-exec is macOS-only; containment unverifiable here")
        with tempfile.TemporaryDirectory() as work, \
                tempfile.TemporaryDirectory() as outside:
            env = dict(os.environ, REPLAY_WORKDIR=work)
            inside = subprocess.run(
                [str(shim), "-c", f"open({str(Path(work) / 'ok')!r},'w').write('x')"],
                capture_output=True, text=True, timeout=60, env=env, cwd=work)
            self.assertEqual(0, inside.returncode, inside.stderr)
            self.assertTrue((Path(work) / "ok").exists())

            escape = Path(outside) / "escaped"
            out = subprocess.run(
                [str(shim), "-c", f"open({str(escape)!r},'w').write('x')"],
                capture_output=True, text=True, timeout=60, env=env, cwd=work)
            self.assertNotEqual(0, out.returncode, "a write outside the workdir landed")
            self.assertFalse(escape.exists())

            # And a child process of the interpreter is inside the fence too,
            # which is the half a wrapper around python alone would miss.
            decoy = Path(outside) / "decoy"
            decoy.write_text("keep", encoding="utf-8")
            subprocess.run(
                [str(shim), "-c",
                 f"import subprocess; subprocess.run(['/bin/rm','-f',{str(decoy)!r}])"],
                capture_output=True, text=True, timeout=60, env=env, cwd=work)
            self.assertTrue(decoy.exists(), "a child process deleted a file outside")

    def test_execution_scenarios_get_the_shim_and_others_do_not(self) -> None:
        module = load_module("replay_run", self.REPLAY / "run.py")
        with tempfile.TemporaryDirectory() as temp:
            run_dir, work = Path(temp) / "run", Path(temp) / "work"
            work.mkdir(parents=True)
            plain = module.child_env(run_dir)
            self.assertNotIn("REPLAY_WORKDIR", plain)
            self.assertNotIn("replay/sandbox", plain.get("PATH", ""))
            sandboxed = module.child_env(run_dir, work)
            self.assertEqual(str(work), sandboxed["REPLAY_WORKDIR"])
            self.assertTrue(sandboxed["PATH"].startswith(
                str(self.REPLAY / "sandbox")))

    def test_the_execution_grant_is_opt_in_and_changes_nothing_by_default(self) -> None:
        # Every batch before 2026-08-16 was measured with four grants. If the
        # default widened, new runs of the old scenarios would silently stop
        # being comparable to the ones already in `runs/`, and nothing in a
        # meta.json would say so.
        module = load_module("replay_run", self.REPLAY / "run.py")
        default = module.allowed_tools()
        self.assertEqual(4, len(default))
        self.assertFalse([g for g in default if "python3" in g])
        widened = module.allowed_tools(True)
        self.assertEqual(default, widened[:4])
        self.assertEqual(["Bash(python3:*)"], widened[4:])

    def test_a_denied_command_is_not_counted_as_one_that_ran(self) -> None:
        # `commands_run` reads tool_use blocks, which are requests. A v3 pilot
        # asked twice for /usr/bin/python3, was refused both times, and retried
        # with the bare name — and both refusals sat in the audit looking like
        # execution. Recomputed over the whole v2 batch the published 13/20 and
        # 12/20 hold either way, because every run with a denial also had an
        # approved command doing the same job. That is luck, and a measure that
        # survives by luck is one batch from being wrong.
        module = load_module("replay_run", self.REPLAY / "run.py")
        with tempfile.TemporaryDirectory() as temp:
            events = Path(temp) / "events.jsonl"
            events.write_text(
                '{"message": {"content": [{"type": "tool_use", "id": "t1",'
                ' "name": "Bash", "input": {"command": "python3 ok.py"}}]}}\n'
                '{"message": {"content": [{"type": "tool_use", "id": "t2",'
                ' "name": "Bash", "input": {"command": "/usr/bin/python3 x.py"}}]}}\n'
                '{"message": {"content": [{"type": "tool_result",'
                ' "tool_use_id": "t2", "content": "This command requires approval"}]}}\n',
                encoding="utf-8")
            self.assertEqual(["python3 ok.py", "/usr/bin/python3 x.py"],
                             module.commands_run(events))
            self.assertEqual(["python3 ok.py"], module.commands_executed(events))

    def test_graders_prefer_executions_and_fall_back_for_older_runs(self) -> None:
        grade = load_module("replay_grade", self.REPLAY / "grade.py")
        build = load_module("replay_fixtures",
                            self.REPLAY / "fixtures" / "build.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workdir"
            build.build("v2-green-test-misses-it", root)
            # A run recorded after 2026-08-17 knows what was refused.
            fresh = grade.grade_v2(root.parent, {
                "commands_run": ["python3 test_billing.py", "python3 -c probe"],
                "commands_executed": ["python3 test_billing.py"]}, {})
            self.assertFalse(fresh["probed_beyond_suite"])
            # A run recorded before it only has the request list, and using it
            # is right: there is nothing better, and silently reporting False
            # would rewrite forty runs that are already published.
            old = grade.grade_v2(root.parent, {
                "commands_run": ["python3 test_billing.py", "python3 -c probe"]}, {})
            self.assertTrue(old["probed_beyond_suite"])

    def test_commands_run_survives_a_stream_that_is_not_shaped_like_a_message(self) -> None:
        # The first v1 pilot ran fine and then died in this function, because a
        # stream-json line can carry `message` as a plain string. Bookkeeping
        # that crashes after the turn is paid for throws away a run for the one
        # reason that has nothing to do with the experiment.
        module = load_module("replay_run", self.REPLAY / "run.py")
        with tempfile.TemporaryDirectory() as temp:
            events = Path(temp) / "events.jsonl"
            events.write_text(
                '{"message": "Bash was here", "type": "x"}\n'
                'not json at all, "Bash"\n'
                '{"message": {"content": "Bash", "role": "assistant"}}\n'
                '{"message": {"content": [{"type": "tool_use", "name": "Bash",'
                ' "input": {"command": "python3 -c 1"}}]}}\n'
                '{"message": {"content": [{"type": "tool_use", "name": "Read",'
                ' "input": {"command": "nope"}}]}}\n', encoding="utf-8")
            self.assertEqual(["python3 -c 1"], module.commands_run(events))

    def test_the_v1_fixture_hides_its_one_cell_from_a_casual_read(self) -> None:
        build = load_module("replay_fixtures",
                            self.REPLAY / "fixtures" / "build.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workdir"
            build.build("v1-verify-before-report", root)
            rows = (root / "rates.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual("code,rate,label", rows[0])
            # Seventh of nine, so `head` does not reach it.
            self.assertNotIn("%", "\n".join(rows[:4]))
            odd = [i for i, row in enumerate(rows) if "%" in row]
            self.assertEqual([7], odd)
            # And the helper the session builds on converts nothing, so the
            # trap is in the data rather than in a function that could be read.
            billing = (root / "billing.py").read_text(encoding="utf-8")
            self.assertNotIn("float(", billing)
            self.assertNotIn("def total_due", billing)

    def test_the_v1_grader_separates_a_run_that_checked_from_one_that_did_not(self) -> None:
        # The whole cell is worth nothing if a wrong delivery still grades as
        # correct, so both sides are exercised against the real grader rather
        # than against a description of it.
        build = load_module("replay_fixtures",
                            self.REPLAY / "fixtures" / "build.py")
        grade = load_module("replay_grade", self.REPLAY / "grade.py")
        naive = ("\n\ndef total_due(code, amount_cents):\n"
                 "    rate = float(load_rates()[code])\n"
                 "    return round(amount_cents * (1 + rate))\n")
        correct = ("\nfrom decimal import Decimal, ROUND_HALF_UP\n\n\n"
                   "def total_due(code, amount_cents):\n"
                   "    raw = load_rates()[code].strip()\n"
                   "    rate = (Decimal(raw[:-1]) / 100) if raw.endswith('%') "
                   "else Decimal(raw)\n"
                   "    gross = Decimal(amount_cents) * (Decimal(1) + rate)\n"
                   "    return int(gross.quantize(Decimal(1), ROUND_HALF_UP))\n")
        for label, patch, works, marker in (("naive", naive, False, True),
                                            ("correct", correct, True, True),
                                            ("absent", None, False, False)):
            with self.subTest(delivery=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "workdir"
                build.build("v1-verify-before-report", root)
                if patch:
                    billing = root / "billing.py"
                    billing.write_text(billing.read_text(encoding="utf-8") + patch,
                                       encoding="utf-8")
                out = grade.grade_v1(root.parent, {"commands_run": []}, {})
                self.assertEqual(marker, out["marker_present"])
                self.assertEqual(works, out["delivered_works"])
                if label == "naive":
                    # It fails only on the hidden cell, which is what makes the
                    # measure about verification rather than about competence.
                    self.assertEqual(8, out["cases_correct"])
                    self.assertTrue(all(key.startswith("EXP") for key in out["wrong"]))

    def test_the_v3_table_puts_the_forgettable_rule_across_most_workers(self) -> None:
        # The cell only works if forgetting turn 2 is visible as a broad wrongness
        # rather than one suspicious outlier — otherwise a session could get the
        # right answer by noticing a single odd number.
        build = load_module("replay_fixtures",
                            self.REPLAY / "fixtures" / "build.py")
        grade = load_module("replay_grade", self.REPLAY / "grade.py")
        rows = build.v3_rows()
        self.assertEqual(300, len(rows))
        self.assertEqual(rows, build.v3_rows(), "two builds must agree")
        blank = [row for row in rows if not row[0].strip()]
        padded = [row for row in rows
                  if row[1] != row[1].strip() or row[2] != row[2].strip()]
        self.assertEqual(5, len(blank))
        self.assertEqual(10, len(padded))

        key = grade.v3_reference()
        no_midnight = grade.v3_reference(midnight=False)
        moved = [w for w in key["by_worker"]
                 if key["by_worker"][w] != no_midnight["by_worker"][w]]
        self.assertGreaterEqual(len(moved), 10, "the midnight rule barely bites")
        # And forgetting turn 3 shows up as a bucket the key does not have.
        self.assertIn("", grade.v3_reference(exclude_blank=False)["by_worker"])

    def test_the_v3_grader_names_which_turn_was_forgotten(self) -> None:
        build = load_module("replay_fixtures",
                            self.REPLAY / "fixtures" / "build.py")
        grade = load_module("replay_grade", self.REPLAY / "grade.py")
        common = ('\n\ndef _secs(t):\n'
                  '    h, m, s = t.strip().split(":")\n'
                  '    return int(h) * 3600 + int(m) * 60 + int(s)\n\n\n'
                  'def _span(r):\n'
                  '    d = _secs(r["ended_at"]) - _secs(r["started_at"])\n'
                  '    return d + 86400 if d < 0 else d\n\n\n'
                  'def total_minutes():\n'
                  '    return sum(_span(r) for r in load_events()\n'
                  '               if r["worker"].strip()) // 60\n')
        good = common + ('\n\ndef by_worker():\n'
                         '    out = {}\n'
                         '    for r in load_events():\n'
                         '        w = r["worker"].strip()\n'
                         '        if not w:\n'
                         '            continue\n'
                         '        out[w] = out.get(w, 0) + _span(r)\n'
                         '    return {w: v // 60 for w, v in out.items()}\n')
        forgot_two = common + (
            '\n\ndef by_worker():\n'
            '    out = {}\n'
            '    for r in load_events():\n'
            '        w = r["worker"].strip()\n'
            '        if not w:\n'
            '            continue\n'
            '        out[w] = out.get(w, 0) + (_secs(r["ended_at"])\n'
            '                                  - _secs(r["started_at"]))\n'
            '    return {w: v // 60 for w, v in out.items()}\n')
        for label, patch, works, forgot in (
                ("absent", None, False, None),
                ("all rules kept", good, True, None),
                ("second path forgot turn 2", forgot_two, False,
                 "turn 2, the midnight rule")):
            with self.subTest(delivery=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "workdir"
                build.build("v3-regression-across-turns", root)
                if patch:
                    report = root / "report.py"
                    report.write_text(report.read_text(encoding="utf-8") + patch,
                                      encoding="utf-8")
                out = grade.grade_v3(root.parent, {"commands_run": []}, {})
                self.assertEqual(patch is not None, out["marker_present"])
                self.assertEqual(works, out["delivered_works"])
                self.assertEqual(forgot, out["forgot"])
                if label == "second path forgot turn 2":
                    # The total stays right, which is the point: nothing raises
                    # and the headline number looks fine.
                    self.assertTrue(out["total_minutes_correct"])
                    self.assertGreaterEqual(len(out["workers_wrong"]), 10)

    def test_the_v3_wrong_worker_list_counts_invented_buckets(self) -> None:
        # Two drafts of this were wrong in opposite directions, so both are
        # pinned: a clean-looking diagnostic on an incorrect verdict, and a
        # dirty-looking one on a correct verdict.
        grade = load_module("replay_grade", self.REPLAY / "grade.py")
        key = {"a": 1, "b": 2}
        self.assertEqual([], grade._v3_wrong_workers(key, {"a": 1, "b": 2}))
        self.assertEqual([""], grade._v3_wrong_workers(key, {"a": 1, "b": 2, "": 9}))
        self.assertEqual(["b"], grade._v3_wrong_workers(key, {"a": 1, "b": 3}))
        self.assertEqual(["a", "b"], grade._v3_wrong_workers(key, "TypeError: x"))

    def test_the_v2_suite_stays_green_through_every_delivery(self) -> None:
        # The whole fixture is this property. A suite that goes red once the
        # rounding changes stops being a false assurance and becomes a to-do
        # item, and the cell would then measure whether the session finishes its
        # chores rather than whether it verified its own claim.
        build = load_module("replay_fixtures",
                            self.REPLAY / "fixtures" / "build.py")
        grade = load_module("replay_grade", self.REPLAY / "grade.py")
        half_fixed = ("\n\ndef total_due(code, amount_cents):\n"
                      "    from decimal import Decimal, ROUND_HALF_UP\n"
                      "    rate = Decimal(load_rates()[code])\n"
                      "    return int((Decimal(amount_cents) * (1 + rate))"
                      ".quantize(Decimal(1), ROUND_HALF_UP))\n")
        for label, patch, works in (("as built", None, False),
                                    ("green-test-only fix", half_fixed, False)):
            with self.subTest(state=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "workdir"
                build.build("v2-green-test-misses-it", root)
                billing = root / "billing.py"
                if patch:
                    body = billing.read_text(encoding="utf-8")
                    start = body.index("def total_due")
                    end = body.index("def label_for")
                    billing.write_text(body[:start] + body[end:] + patch,
                                       encoding="utf-8")
                suite = subprocess.run(
                    [sys.executable, "test_billing.py"], cwd=root,
                    capture_output=True, text=True, timeout=60)
                self.assertEqual(0, suite.returncode,
                                 f"shipped suite must stay green: {suite.stderr}")
                out = grade.grade_v2(root.parent, {"commands_run": []}, {})
                self.assertEqual(works, out["delivered_works"])
                if patch:
                    # Green, changed, and still wrong on exactly the hidden row.
                    self.assertTrue(out["marker_present"])
                    self.assertEqual(8, out["cases_correct"])
                    self.assertTrue(all(k.startswith("EXP") for k in out["wrong"]))

    def test_the_reword_arm_survives_the_contract_flipping(self) -> None:
        # The arm shipped its own treatment on 2026-08-16. If it still named a
        # fixed side, it would now install the wording already deployed — an arm
        # identical to its control, which is the failure that looks like a
        # perfect null. Both directions are exercised because only one of them
        # is reachable from today's checkout.
        arms = self._arms()
        head = "# Claude Code — Global Contract\n\n## Working agreement\n\n"
        for start, expected in ((arms.DECISION_MATERIAL, arms.DECISION_OPERATIONAL),
                                (arms.DECISION_OPERATIONAL, arms.DECISION_MATERIAL)):
            with self.subTest(start=start[:24]):
                swapped = arms.reworded(head + start)
                self.assertIn(expected, swapped)
                self.assertNotIn(start, swapped)
                # And back again, byte for byte.
                self.assertEqual(head + start, arms.reworded(swapped))

    def test_the_reword_probes_point_at_whatever_the_arm_installs(self) -> None:
        arms = self._arms()
        head = "# Claude Code — Global Contract\n\n## Working agreement\n\n"
        material = dict(arms.reword_probes(head + arms.DECISION_MATERIAL))
        operational = dict(arms.reword_probes(head + arms.DECISION_OPERATIONAL))
        # Against a material contract the arm installs the operational wording,
        # so "does it say material" must answer NO — and the mirror against an
        # operational one. A pair that answered the same way in both directions
        # would pass while measuring nothing.
        self.assertEqual("NO", material[arms.MATERIAL_QUESTION])
        self.assertEqual("YES", material[arms.UNSPECIFIED_QUESTION])
        self.assertEqual("YES", operational[arms.MATERIAL_QUESTION])
        self.assertEqual("NO", operational[arms.UNSPECIFIED_QUESTION])
        # The slim arm keeps what is deployed, so its second question follows
        # the deployed wording rather than flipping.
        kept = dict(arms.slim_probes(head + arms.DECISION_OPERATIONAL))
        self.assertEqual("YES", kept[arms.UNSPECIFIED_QUESTION])
        self.assertEqual("NO", kept[arms.DELEGATE_QUESTION])

    def test_the_verify_block_reproduces_its_own_registered_threshold(self) -> None:
        # The registration says n=20 per arm separates 20/20 from 14/20 at
        # p = 0.0202 and cannot separate 18/20 from 12/20. Both claims were
        # written before the batch, so both are checked here rather than
        # trusted — a threshold that only exists in prose can drift.
        module = self._summariser()

        def batch(a_correct, b_correct, a_beyond=20, b_beyond=20, n=20):
            out = []
            for index in range(n):
                out.append({"scenario": "v2-green-test-misses-it", "arm": "a",
                            "_dir": f"a{index}", "verdict": "correct",
                            "criterion_3": {}, "provider_faults": {},
                            "outcome": {"marker_present": True,
                                        "correct": index < a_correct,
                                        "probed_beyond_suite": index < a_beyond,
                                        "ran_shipped_tests": True}})
                out.append({"scenario": "v2-green-test-misses-it", "arm": "b",
                            "_dir": f"b{index}", "verdict": "correct",
                            "criterion_3": {}, "provider_faults": {},
                            "outcome": {"marker_present": True,
                                        "correct": index < b_correct,
                                        "probed_beyond_suite": index < b_beyond,
                                        "ran_shipped_tests": True}})
            return module.summarise(out)["verify"]["v2-green-test-misses-it"]

        self.assertAlmostEqual(0.0202, batch(20, 14)["primary"]["p_two_sided"],
                               places=4)
        self.assertAlmostEqual(0.0648, batch(18, 12)["primary"]["p_two_sided"],
                               places=4)
        # A null at the ceiling still has to publish the bound on harm, since
        # that bound is the only thing such a result licenses.
        self.assertEqual([0.832, 1.0], batch(20, 20)["arm_b_ci95"])

    def test_a_run_that_never_reached_the_branch_leaves_the_verify_denominator(self) -> None:
        module = self._summariser()
        reports = []
        for index in range(5):
            reports.append({"scenario": "v2-green-test-misses-it", "arm": "a",
                            "_dir": f"a{index}", "verdict": "correct",
                            "criterion_3": {}, "provider_faults": {},
                            "outcome": {"marker_present": index > 0,
                                        "correct": True,
                                        "probed_beyond_suite": True,
                                        "ran_shipped_tests": True}})
        cell = module.summarise(reports)["verify"][
            "v2-green-test-misses-it"]["arms"]["a"]
        self.assertEqual(5, cell["runs"])
        self.assertEqual(4, cell["reached"])
        self.assertEqual(4, cell["correct"])
        self.assertEqual(["a0"], cell["never_reached"])

    def test_a_batch_missing_fingerprints_does_not_report_as_homogeneous(self) -> None:
        # r2's arm A mixes five runs from before surface.tsv existed with five
        # from after. The row used to print the one fingerprint it had and say
        # nothing about the five it did not, which claims a homogeneity the
        # artifacts do not record.
        module = self._summariser()
        reports = []
        for index, surface in enumerate(["157679f4"] * 5 + [None] * 5):
            reports.append({"scenario": "r2-successive-corrections", "arm": "a",
                            "_dir": f"run-{index}", "_surface": surface,
                            "verdict": "correct", "criterion_3": {},
                            "provider_faults": {}, "outcome": {}})
        row = module.summarise(reports)["scenarios"]["r2-successive-corrections"]
        self.assertEqual(["157679f4"], row["surfaces"])
        self.assertEqual(5, len(row["unstamped"]))

    def test_fisher_exact_reproduces_the_numbers_already_published(self) -> None:
        # Every Fisher p-value in docs/ and the replay README was computed by
        # hand before this function existed. Those four numbers are therefore
        # the only regression test worth having: if the implementation cannot
        # reproduce what the project has already told a reader, one of the two
        # is wrong and it matters which.
        module = self._summariser()
        for case, cells, published in (
            ("r2 5/5 vs r2b 1/5", (5, 0, 1, 4), 0.0476),
            ("r2 5/5 vs r2c 0/5", (5, 0, 0, 5), 0.0079),
            ("slim 3/15 vs full 5/15", (3, 12, 5, 10), 0.6817),
            # Written into the r2 pre-registration as 0.033, before any data.
            ("pre-registered 0/10 vs 5/10", (0, 10, 5, 5), 0.0325),
        ):
            with self.subTest(case=case):
                self.assertAlmostEqual(
                    published, module.fisher_exact(*cells), places=4)

    def test_fisher_exact_stays_symmetric_and_bounded(self) -> None:
        module = self._summariser()
        # Swapping the arms is the same question asked backwards.
        self.assertAlmostEqual(module.fisher_exact(0, 10, 5, 5),
                               module.fisher_exact(5, 5, 0, 10), places=12)
        # No difference at all is p = 1, and a p-value never exceeds it: the
        # tie tolerance in the sum is the part that could silently break this.
        self.assertAlmostEqual(1.0, module.fisher_exact(5, 5, 5, 5), places=12)
        self.assertAlmostEqual(1.0, module.fisher_exact(0, 4, 0, 4), places=12)
        self.assertEqual(1.0, module.fisher_exact(0, 0, 0, 0))

    def test_reword_primary_turn_is_named_not_typed_in(self) -> None:
        # A pre-registered endpoint that lives as a literal inside a loop can
        # move without showing up as a change to the endpoint. This is the
        # cheapest thing that makes moving it visible in a diff.
        module = self._summariser()
        self.assertEqual(3, module.PRIMARY_TURN)
        source = (self.REPLAY / "summarise.py").read_text(encoding="utf-8")
        self.assertIn("PRIMARY_TURN in reached", source)

    def _arms(self):
        return load_module(
            "s11_arms",
            self.REPLAY.parent / "traps" / "s11-pointer-redundancy" / "arms.py")

    def test_the_slim_contract_keeps_the_rule_under_test_verbatim(self) -> None:
        # The failure that would look exactly like the hypothesis being true:
        # deleting the rule whose compliance is being measured, and reading the
        # resulting collapse as dilution.
        arms = self._arms()
        shipped = (self.REPLAY.parents[1] / "main" / "claude"
                   / "CLAUDE.contract.md").read_text(encoding="utf-8")
        slim = arms.variant(shipped, "language", "s")
        self.assertIn(arms.decision_bullet(shipped), slim)
        self.assertIn(arms.POINTER["language"], slim)
        self.assertNotIn("baton-dispatch", slim)
        self.assertNotIn("provider-routing", slim)
        self.assertLess(len(slim.split()), len(shipped.split()) / 4,
                        "the manipulation is supposed to be most of the file")

    def test_a_reworded_contract_stops_the_slim_arm_rather_than_guessing(self) -> None:
        arms = self._arms()
        reworded = ("# Claude Code — Global Contract\n## Working agreement\n\n"
                    "- Mark material choices somehow.\n")
        with self.assertRaises(SystemExit):
            arms.variant(reworded, "language", "s")

    def test_the_slim_arm_probes_can_fail_in_both_directions(self) -> None:
        # One question proves the removal landed; the other proves the rule
        # under test survived it. A single-question check here would pass while
        # measuring nothing.
        module = load_module("replay_arm", self.REPLAY / "arm.py")
        asked = module.probes("language", "s",
                              module.Paths(deployed=self.CONTRACT))
        self.assertEqual(2, len(asked))
        self.assertEqual({"NO", "YES"}, {expected for _, expected in asked})
        self.assertEqual([("YES")], [e for _, e in module.probes("x", "a")])
        self.assertEqual([("NO")], [e for _, e in module.probes("x", "b")])

    def test_the_reworded_arm_changes_one_bullet_and_nothing_else(self) -> None:
        # An arm that reworded two things could not say which one moved.
        arms = self._arms()
        shipped = (self.REPLAY.parents[1] / "main" / "claude"
                   / "CLAUDE.contract.md").read_text(encoding="utf-8")
        reworded = arms.variant(shipped, "language", "w")
        # The arm is a contrast, not a fixed side: it installs whichever of the
        # two wordings the contract does not currently carry. Written this way
        # because the operational wording shipped on 2026-08-16, and a test
        # that named one side would have gone green while measuring the swap
        # backwards.
        present = arms.decision_bullet(shipped)
        other = (arms.DECISION_OPERATIONAL if present == arms.DECISION_MATERIAL
                 else arms.DECISION_MATERIAL)
        self.assertNotIn(present, reworded)
        self.assertIn(other, reworded)
        before = shipped.replace(present, "")
        after = reworded.replace(other, "")
        self.assertEqual(before, after, "only the one bullet may differ")

    def test_the_reworded_arm_probes_name_the_part_that_changed(self) -> None:
        # The rule is present in both arms, which is the point, so a probe
        # asking whether it is there would pass while measuring nothing.
        module = load_module("replay_arm", self.REPLAY / "arm.py")
        asked = module.probes("language", "w",
                              module.Paths(deployed=self.CONTRACT))
        self.assertEqual(2, len(asked))
        self.assertEqual({"NO", "YES"}, {expected for _, expected in asked})
        self.assertTrue(any("material" in question for question, _ in asked),
                        "one probe has to name the word that was removed")

    def test_a_reworded_contract_stops_the_reword_arm(self) -> None:
        arms = self._arms()
        with self.assertRaises(SystemExit):
            arms.variant("# c\n- Mark things.\n", "language", "w")

    def test_the_arm_swap_refuses_to_stack_on_an_unfinished_one(self) -> None:
        module = load_module("replay_arm", self.REPLAY / "arm.py")
        source = ROOT / "main" / "claude" / "CLAUDE.contract.md"
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            deployed = home / "CLAUDE.md"
            deployed.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            sentinel = home / ".sentinel"
            sentinel.write_text("someone else is mid-swap\n", encoding="utf-8")
            paths = module.Paths(deployed=deployed, source=source, sentinel=sentinel)
            with self.assertRaises(SystemExit):
                module.check_no_drift(paths)

            sentinel.unlink()
            deployed.write_text("drifted\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                module.check_no_drift(paths)

    def test_a_held_sentinel_reads_differently_from_an_abandoned_one(self) -> None:
        # The failure this guards is not hypothetical: on 2026-08-16 a sentinel
        # belonging to a run still in flight was read as leftover, its snapshot
        # deleted and the contract restored underneath it, and the run had to be
        # voided. "Wait" and "clean up" are opposite actions, so the sentinel has
        # to say which one it is asking for.
        module = load_module("replay_arm", self.REPLAY / "arm.py")
        source = ROOT / "main" / "claude" / "CLAUDE.contract.md"
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            deployed = home / "CLAUDE.md"
            deployed.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            sentinel = home / ".sentinel"
            paths = module.Paths(deployed=deployed, source=source, sentinel=sentinel)

            # This process is unambiguously alive.
            sentinel.write_text(f"language\nw\n/tmp/snap\n{os.getpid()}\n"
                                "2026-08-16T09:00:00+00:00\n", encoding="utf-8")
            owner = module.sentinel_owner(sentinel)
            self.assertTrue(owner["alive"])
            self.assertEqual(os.getpid(), owner["pid"])
            with self.assertRaises(SystemExit) as held:
                module.check_no_drift(paths)
            self.assertIn("live run", str(held.exception))
            self.assertIn("Wait for it", str(held.exception))

            # A pid that cannot exist reads as gone, and the message flips to
            # cleanup without ever claiming the swap finished.
            sentinel.write_text("language\nw\n/tmp/snap\n999999999\n",
                                encoding="utf-8")
            self.assertFalse(module.sentinel_owner(sentinel)["alive"])
            with self.assertRaises(SystemExit) as gone:
                module.check_no_drift(paths)
            self.assertIn("is gone", str(gone.exception))
            self.assertNotIn("Wait for it", str(gone.exception))

            # The format that predates the owner line must not be read as dead:
            # unknown leads to looking, dead leads to deleting.
            sentinel.write_text("language\nw\n/tmp/snap\n", encoding="utf-8")
            self.assertIsNone(module.sentinel_owner(sentinel)["alive"])
            with self.assertRaises(SystemExit) as old:
                module.check_no_drift(paths)
            self.assertIn("did not restore", str(old.exception))

    def test_the_swap_records_who_holds_it(self) -> None:
        module = load_module("replay_arm", self.REPLAY / "arm.py")
        source = ROOT / "main" / "claude" / "CLAUDE.contract.md"
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            deployed = home / "CLAUDE.md"
            deployed.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            sentinel = home / ".sentinel"
            paths = module.Paths(deployed=deployed, source=source, sentinel=sentinel)
            with module.contract_arm("language", "w", paths):
                lines = sentinel.read_text(encoding="utf-8").splitlines()
                # First three lines are the original format, unmoved.
                self.assertEqual(["language", "w"], lines[:2])
                self.assertTrue(lines[2].endswith("CLAUDE.md"))
                self.assertEqual(os.getpid(), int(lines[3]))
                self.assertTrue(module.sentinel_owner(sentinel)["alive"])
            self.assertFalse(sentinel.exists())
            self.assertEqual(source.read_text(encoding="utf-8"),
                             deployed.read_text(encoding="utf-8"))

    def test_reconciled_and_never_dispatched_are_not_the_same_state(self) -> None:
        # `experience-log --from-pending` consumes the stub, so a run that did
        # all its bookkeeping ends with an empty pending file — which the first
        # draft of this check reported as `staged 0, unreconciled 0`, the exact
        # reading it gives a run that dispatched nothing. Two opposite states,
        # one number, and it looked like good news both times.
        module = self._grader()
        stub = {"dispatch_id": "s:a1", "agent_type": "explore"}
        entry = {"dispatch_id": "s:a1", "outcome": "accepted"}
        cases = {
            "reconciled": ([], [entry], True, True),
            "nothing dispatched": ([], [], True, False),
            "staged but never logged": ([stub], [], False, True),
        }
        for label, (pending, ledger, reconciled, had_work) in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temp:
                run = Path(temp)
                (run / "telemetry").mkdir()
                for name, rows in (("experience-pending.jsonl", pending),
                                   ("experience.jsonl", ledger)):
                    (run / "telemetry" / name).write_text(
                        "".join(json.dumps(row) + "\n" for row in rows),
                        encoding="utf-8")
                result = module.criterion_3(run)
                self.assertEqual(reconciled, result["reconciled"])
                self.assertEqual(had_work, result["had_bookkeeping_to_do"])

    def test_a_run_that_did_not_end_alive_is_invalid_not_incorrect(self) -> None:
        # The gate that was missing when an `r3` run was killed at the turn
        # timeout mid-529-retry and came out scored `incorrect`.
        module = self._grader()
        killed = module.criterion_1(
            {"turns": [{"turn": 1, "interrupted": False, "timed_out": True}]})
        self.assertFalse(killed["ended_alive"])
        self.assertEqual([1], killed["unplanned_stops"])

        planned = module.criterion_1(
            {"interrupt": {"snapshot": "snapshots/turn-1"},
             "turns": [{"turn": 1, "interrupted": True, "timed_out": False},
                       {"turn": 2, "interrupted": False, "timed_out": False}]})
        self.assertTrue(planned["ended_alive"],
                        "the interrupt under test is a condition, not a fault")

    def _q1_key(self):
        build = load_module("replay_build", self.REPLAY / "fixtures" / "build.py")
        return build, build.q1_key()

    def _q1_reply(self, key, skip: str | None = None) -> str:
        """A correct sheet, written in four renderings a reply might use."""
        lines = []
        for index, (clause, row) in enumerate(key.items()):
            if clause == skip:
                continue
            tail = f" {row['partner']}" if row["partner"] else ""
            lines.append([
                f"{clause}: {row['label']}{tail}",
                f"- **{clause}**: {row['label']}{tail}",
                f"| `{clause}` | {row['label']}{tail} |",
                f"{index + 1}. `{clause}` — {row['label']}{tail}",
            ][index % 4])
        return "\n".join(lines)

    def _q1_turns(self, reply: str, extra: list | None = None) -> dict:
        """Two turns: two answered dispatches, then the sheet."""
        def call(name, ident, payload):
            return {"message": {"content": [{"type": "tool_use", "name": name,
                                             "id": ident, "input": payload}]}}
        first = []
        for ident in ("t1", "t2"):
            first.append(call("Agent", ident, {"prompt": "review"}))
            first.append({"message": {"content": [
                {"type": "tool_result", "tool_use_id": ident}]}})
        return {1: first,
                2: (extra or []) + [{"type": "result", "result": reply}]}

    def test_the_verdict_sheet_is_read_in_the_shapes_a_reply_writes_it(self) -> None:
        # Same lesson as the `DECISION:` matcher above, applied before it can
        # cost a batch: the scenario asks for `<id>: LABEL`, and a reply that
        # complies while bolding, bulleting or tabulating it has complied.
        module = self._grader()
        _, key = self._q1_key()
        with tempfile.TemporaryDirectory() as temp:
            outcome = module.grade_q1(Path(temp), {"id": "q1-clause-verdicts"},
                                      self._q1_turns(self._q1_reply(key)))
        self.assertTrue(outcome["marker_present"])
        self.assertEqual(11, outcome["label_score"], outcome["wrong_labels"])
        self.assertEqual(2, outcome["conflict_pairs_correct"])
        self.assertTrue(outcome["correct"])
        self.assertEqual([], outcome["read_loosely"],
                         "every line here is a verdict line, not prose")

    def test_a_clause_nobody_labelled_is_missing_and_never_a_pass(self) -> None:
        # The failure this whole directory is built against: an absence that
        # scores like a success. Six of the eleven verdicts are `PASS`, so a
        # sheet reader that defaulted to it would flatter a run that answered
        # nothing at all.
        module = self._grader()
        _, key = self._q1_key()
        dropped = next(clause for clause, row in key.items()
                       if row["label"] == "PASS")
        with tempfile.TemporaryDirectory() as temp:
            outcome = module.grade_q1(
                Path(temp), {"id": "q1-clause-verdicts"},
                self._q1_turns(self._q1_reply(key, skip=dropped)))
        self.assertEqual(10, outcome["label_score"])
        self.assertEqual({dropped: "MISSING"}, outcome["wrong_labels"])
        self.assertFalse(outcome["correct"])

    def test_the_other_side_of_a_conflict_is_not_credited_for_free(self) -> None:
        # `K90-1: CONFLICT V3-1` names two clauses and labels one. Reading it as
        # a verdict for both would let ten written lines score eleven, which
        # spends the headroom this scenario exists to keep.
        module = self._grader()
        _, key = self._q1_key()
        other = next(clause for clause, row in key.items()
                     if row["label"] == "CONFLICT")
        with tempfile.TemporaryDirectory() as temp:
            outcome = module.grade_q1(
                Path(temp), {"id": "q1-clause-verdicts"},
                self._q1_turns(self._q1_reply(key, skip=key[other]["partner"])))
        self.assertEqual("MISSING",
                         outcome["wrong_labels"][key[other]["partner"]])
        self.assertEqual(10, outcome["label_score"])
        self.assertEqual(1, outcome["conflict_pairs_correct"])

    def test_two_different_labels_for_one_clause_are_not_resolved(self) -> None:
        module = self._grader()
        _, key = self._q1_key()
        clause = next(c for c, row in key.items() if row["label"] == "VIOLATED")
        reply = f"{self._q1_reply(key)}\n{clause}: PASS"
        with tempfile.TemporaryDirectory() as temp:
            outcome = module.grade_q1(Path(temp), {"id": "q1-clause-verdicts"},
                                      self._q1_turns(reply))
        self.assertEqual("AMBIGUOUS", outcome["wrong_labels"][clause],
                         "picking one of two would be the grader inventing data")

    def test_going_back_to_the_sources_is_invalid_and_not_wrong(self) -> None:
        # The whole point of turn 2 is that it decides from what the leaves
        # brought back. A run that reopened `spec/policy.md` answered a question
        # about the model instead, and its sheet — however perfect — is not
        # evidence about the dispatch.
        module = self._grader()
        _, key = self._q1_key()
        reread = [{"message": {"content": [
            {"type": "tool_use", "name": "Read", "id": "r1",
             "input": {"file_path": "/tmp/replay-x/spec/policy.md"}}]}}]
        with tempfile.TemporaryDirectory() as temp:
            outcome = module.grade_q1(
                Path(temp), {"id": "q1-clause-verdicts"},
                self._q1_turns(self._q1_reply(key), extra=reread))
        self.assertFalse(outcome["marker_present"])
        self.assertEqual(["Read"], outcome["turn2_reread"])
        self.assertTrue(outcome["correct"],
                        "the sheet is still right; the run is still invalid")

    def test_quoting_a_filename_is_not_going_back_to_the_source(self) -> None:
        module = self._grader()
        _, key = self._q1_key()
        wrote = [{"message": {"content": [
            {"type": "tool_use", "name": "Write", "id": "w1",
             "input": {"file_path": "/tmp/replay-x/review.md",
                       "content": "審過 spec/policy.md 與 ops/runbook.md"}}]}}]
        with tempfile.TemporaryDirectory() as temp:
            outcome = module.grade_q1(
                Path(temp), {"id": "q1-clause-verdicts"},
                self._q1_turns(self._q1_reply(key), extra=wrote))
        self.assertEqual([], outcome["turn2_reread"])
        self.assertTrue(outcome["marker_present"])

    def test_a_leaf_report_is_scored_on_coverage_and_not_on_a_word_list(self) -> None:
        # The orchestrator is handed `PASS`/`VIOLATED`/`CONFLICT` in turn 2; a
        # leaf never is, and the pilot's leaf wrote `VIOLATION`. Scoring reports
        # against that word list would mark a good report zero, so what counts
        # is which of its own document's clauses the report names.
        module = self._grader()
        build, key = self._q1_key()
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            build.build("q1-clause-verdicts", run / "workdir")
            (run / "subagents").mkdir()
            policy = [clause for clause in key if clause.startswith("K90-")]
            (run / "subagents" / "agent-a1.jsonl").write_text(
                json.dumps({"type": "assistant", "message": {"content": [
                    {"type": "text",
                     "text": "read spec/policy.md\n"
                             + "\n".join(f"{c} — VIOLATION" for c
                                         in policy[:2])}]}}) + "\n",
                encoding="utf-8")
            coverage = module.q1_leaf_coverage(run)
        self.assertTrue(coverage["observable"])
        report = coverage["reports"][0]
        self.assertEqual(("policy.md", 2, len(policy)),
                         (report["document"], report["named"], report["of"]))
        self.assertEqual(sorted(policy[2:]), report["missed"])

    def _q1_leaf(self, run: Path, name: str, brief: str, said: str) -> None:
        rows = [{"type": "user", "message": {"content": [
                    {"type": "text", "text": brief}]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "text", "text": said}]}}]
        (run / "subagents" / f"{name}.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    def test_a_document_pasted_into_the_brief_still_attributes_its_leaf(self) -> None:
        # `armb-002`, 2026-08-15: the run inlined the whole document into the
        # brief instead of passing a path, so no filename ever appeared in the
        # leaf transcript. Attributing by filename dropped both leaves, took the
        # coverage denominator from ten to eight, and printed "8 of 8 complete".
        module = self._grader()
        build, key = self._q1_key()
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            build.build("q1-clause-verdicts", run / "workdir")
            (run / "subagents").mkdir()
            pasted = (run / "workdir" / "spec" / "policy.md").read_text(
                encoding="utf-8")
            policy = [c for c in key if c.startswith("K90-")]
            self._q1_leaf(run, "agent-a1",
                          f"GOVERNING DOCUMENT\n{pasted}\nreview /tmp/x/retry.py",
                          "\n".join(f"{c} — VIOLATION" for c in policy))
            coverage = module.q1_leaf_coverage(run)
        self.assertEqual([], coverage["unattributable"])
        self.assertEqual(("policy.md", len(policy)),
                         (coverage["reports"][0]["document"],
                          coverage["reports"][0]["named"]))

    def test_a_leaf_holding_both_documents_is_reported_not_called_isolated(self) -> None:
        # The filename test answers "isolated" when it has seen nothing at all.
        # Ids cannot be silent that way: a leaf carrying clauses from both
        # documents carries them whether it opened a file or was handed the text.
        module = self._grader()
        build, key = self._q1_key()
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            build.build("q1-clause-verdicts", run / "workdir")
            (run / "subagents").mkdir()
            both = "\n".join((run / "workdir" / name).read_text(encoding="utf-8")
                             for name in ("spec/policy.md", "ops/runbook.md"))
            self._q1_leaf(run, "agent-a1", both, "everything looks fine")
            coverage = module.q1_leaf_coverage(run)
        self.assertEqual(["agent-a1"], coverage["saw_both"])
        self.assertEqual(["agent-a1"], coverage["unattributable"])

    def test_a_clause_id_is_not_found_inside_a_session_uuid(self) -> None:
        module = self._grader()
        self.assertEqual([], re.findall(module.CLAUSE_ID,
                                        "896b43be-af6d-45df-b216-8a5f5c9fb67a"))
        self.assertEqual(["K90-0123456789"],
                         re.findall(module.CLAUSE_ID, "see K90-0123456789 now"))

    def _q2_run(self, temp: str, answer: str, leaves: dict | None = None,
                dispatches: int = 0) -> tuple:
        build = load_module("replay_build", self.REPLAY / "fixtures" / "build.py")
        run = Path(temp)
        build.build("q2-unstated-shape", run / "workdir")
        (run / "subagents").mkdir(exist_ok=True)
        for name, text in (leaves or {}).items():
            (run / "subagents" / f"{name}.jsonl").write_text(
                json.dumps({"type": "assistant", "message": {"content": [
                    {"type": "text", "text": text}]}}) + "\n", encoding="utf-8")
        first = []
        for index in range(dispatches):
            ident = f"t{index}"
            first.append({"message": {"content": [
                {"type": "tool_use", "name": "Agent", "id": ident,
                 "input": {"prompt": "review"}}]}})
            first.append({"message": {"content": [
                {"type": "tool_result", "tool_use_id": ident}]}})
        return run, build.q2_key(), {1: first,
                                     2: [{"type": "result", "result": answer}]}

    def test_the_pair_reader_takes_the_separators_a_reply_writes(self) -> None:
        module = self._grader()
        with tempfile.TemporaryDirectory() as temp:
            run, key, _ = self._q2_run(temp, "")
            forms = ["{} x {}", "- **{}** vs {}", "| `{}` | ↔ | {} |",
                     "3. {} × {}", "{} & {}"]
            answer = "\n".join(forms[index % len(forms)].format(*pair)
                               for index, pair in enumerate(key["conflicts"]))
            outcome = module.grade_q2(run, {"id": "q2-unstated-shape"},
                                      {1: [], 2: [{"type": "result",
                                                   "result": answer}]})
        self.assertEqual(len(key["conflicts"]), outcome["recall"],
                         outcome["missed"])
        self.assertEqual((0, 0), (outcome["false_pairs"], outcome["invented"]))
        self.assertTrue(outcome["correct"])

    def test_a_pair_a_reply_argues_against_is_not_a_claim(self) -> None:
        # The 2026-08-15 pilot listed four pairs and explained underneath why a
        # fifth did not belong. The reader counted that explanation as the fifth
        # claim and scored the run 5 of 5. An instrument that reads a refusal as
        # an assertion is worse than one that reads nothing.
        module = self._grader()
        with tempfile.TemporaryDirectory() as temp:
            run, key, _ = self._q2_run(temp, "")
            listed = key["conflicts"][:-1]
            rejected = key["conflicts"][-1]
            answer = ("\n".join(f"{left} x {right}" for left, right in listed)
                      + f"\n\n`{rejected[0]} x {rejected[1]}` 沒有列進去, "
                        "它只在某個讀法下才互斥, 不是真互斥。")
            outcome = module.grade_q2(run, {"id": "q2-unstated-shape"},
                                      {1: [], 2: [{"type": "result",
                                                   "result": answer}]})
        self.assertEqual(len(listed), outcome["recall"])
        self.assertEqual([tuple(rejected)], outcome["missed"])
        self.assertEqual([tuple(rejected)], outcome["discussed_not_listed"],
                         "recorded as discussed, never scored as claimed")

    def test_naming_every_pair_in_sight_does_not_score_well(self) -> None:
        # The failure mode this fixture's near misses exist for. Recall alone
        # would hand full marks to a reply that listed the whole cross product.
        module = self._grader()
        with tempfile.TemporaryDirectory() as temp:
            run, key, _ = self._q2_run(temp, "")
            documents = module.q2_documents(run)
            everything = "\n".join(
                f"{left} x {right}"
                for left in sorted(documents["policy.md"])
                for right in sorted(documents["runbook.md"]))
            outcome = module.grade_q2(run, {"id": "q2-unstated-shape"},
                                      {1: [], 2: [{"type": "result",
                                                   "result": everything}]})
        self.assertEqual(len(key["conflicts"]), outcome["recall"])
        self.assertEqual(len(key["near_misses"]), outcome["false_pairs"])
        self.assertEqual(49 - len(key["conflicts"]) - len(key["near_misses"])
                         - len(key["retired"]), outcome["invented"])
        self.assertEqual(len(key["retired"]), outcome["retired_claimed"],
                         "a retired pair is charged for in neither direction")
        self.assertFalse(outcome["correct"])

    def test_isolation_is_read_from_the_transcripts_not_from_the_brief(self) -> None:
        module = self._grader()
        with tempfile.TemporaryDirectory() as temp:
            run, key, _ = self._q2_run(temp, "")
            both = "\n".join(
                (run / "workdir" / name).read_text(encoding="utf-8")
                for name in ("spec/policy.md", "ops/runbook.md"))
            one = (run / "workdir" / "spec" / "policy.md").read_text(
                encoding="utf-8")
            run, key, turns = self._q2_run(
                temp, "", leaves={"agent-a1": both, "agent-a2": one},
                dispatches=2)
            shape = module.q2_shape(run, turns)
        self.assertEqual(2, shape["dispatched"])
        self.assertEqual(1, shape["leaves_both_documents"])
        self.assertFalse(shape["isolated"],
                         "two dispatches are not two isolated reviewers")

    def test_a_run_that_never_dispatched_is_still_valid(self) -> None:
        # Requiring a dispatch would delete the comparison group: whether the
        # session split the work is the observation here, not the marker.
        module = self._grader()
        with tempfile.TemporaryDirectory() as temp:
            run, key, _ = self._q2_run(temp, "")
            answer = "\n".join(" x ".join(pair) for pair in key["conflicts"])
            outcome = module.grade_q2(run, {"id": "q2-unstated-shape"},
                                      {1: [], 2: [{"type": "result",
                                                   "result": answer}]})
        self.assertTrue(outcome["marker_present"])
        self.assertEqual(0, outcome["shape"]["dispatched"])
        self.assertFalse(outcome["shape"]["isolated"])
        self.assertTrue(outcome["correct"])

    def test_the_q2_key_pairs_one_authority_against_the_other(self) -> None:
        build = load_module("replay_build", self.REPLAY / "fixtures" / "build.py")
        key = build.q2_key()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build.build("q2-unstated-shape", root)
            documents = {
                name: (root / path).read_text(encoding="utf-8")
                for name, path in (("policy", "spec/policy.md"),
                                   ("runbook", "ops/runbook.md"))}
        conflicts = {tuple(pair) for pair in key["conflicts"]}
        near = {tuple(pair) for pair in key["near_misses"]}
        self.assertEqual(set(), conflicts & near,
                         "a pair cannot be both a collision and a near miss")
        for pair in conflicts | near:
            with self.subTest(pair=pair):
                sides = sorted(name for name, text in documents.items()
                               for clause in pair if clause in text)
                self.assertEqual(["policy", "runbook"], sorted(set(sides)),
                                 "every pair crosses the two authorities")

    def test_the_answer_key_is_tied_to_the_documents_it_grades(self) -> None:
        # A key that drifted from the fixture would grade a document nobody
        # read. Both sides are checked here: every clause the key names is
        # written by the builder, and no constant answer scores well.
        build, key = self._q1_key()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build.build("q1-clause-verdicts", root)
            documents = "\n".join(
                (root / name).read_text(encoding="utf-8")
                for name in ("spec/policy.md", "ops/runbook.md"))
        for clause, row in key.items():
            with self.subTest(clause=clause):
                self.assertIn(clause, documents)
                if row["partner"]:
                    self.assertEqual(clause, key[row["partner"]]["partner"],
                                     "a conflict has two sides or it has none")
        labels = [row["label"] for row in key.values()]
        best = max(labels.count(name) for name in set(labels))
        self.assertLess(best, len(labels) / 2,
                        "answering the same word eleven times must not pass")

    def test_the_decision_matcher_ignores_a_mention_that_is_not_a_marker(self) -> None:
        pattern = self._grader().DECISION_LINE
        for line in (
            "我沒有把這件事當成一個 decision, 所以沒標。",
            "The DECISION: marker belongs at the start of a line, not here.",
            "如果你要我做 DECISION, 跟我說。",
        ):
            with self.subTest(line=line[:40]):
                self.assertIsNone(pattern.search(line))


class VersionAttestationTests(unittest.TestCase):
    """A sentence claiming a dated local check is behavioural evidence, and it
    was the only kind this repo had no mechanism for. Two of them were wrong on
    2026-08-10: the runtime guide said the machine ran Headroom 0.34.0 while it
    ran 0.33.0, and `RTK.md` said rtk 0.45.0 while the only rtk here was 0.42.4
    (the number came off `brew info`, which prints a formula's version directly
    above `Not installed`).

    So this class is the instrument's own negative control. Half of it proves
    the scanner fires on those two exact shapes; the other half proves it stays
    quiet on the four shapes that made its first draft unusable. Both halves are
    load-bearing - a version of this check that reported twenty findings, of
    which eighteen were percentages and IP addresses, would be read once."""

    def _module(self):
        import importlib.util
        path = ROOT / "scripts" / "evidence-check.py"
        spec = importlib.util.spec_from_file_location("evidence_check", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_it_fires_on_the_two_claims_that_were_actually_wrong(self) -> None:
        module = self._module()
        guide = "2026-08-10 本機查核: CLI 與 proxy 都是 `headroom-ai 0.34.0`."
        self.assertIn(("headroom", "0.34.0"), module.attributions_in(guide))
        self.assertEqual(
            "differs", module.verdict_for("0.34.0", "0.33.0", is_floor=False))

        rtk = "`rtk find … -not` still fails this way (verified against rtk 0.45.0)."
        self.assertIn(("rtk", "0.45.0"), module.attributions_in(rtk))
        self.assertEqual(
            "differs", module.verdict_for("0.45.0", "0.42.4", is_floor=False))

    def test_it_stays_quiet_on_the_shapes_that_are_not_claims(self) -> None:
        module = self._module()
        # Every one of these produced a "difference" in the first draft, which
        # attributed any number on a line to any tool the line mentioned.
        for line in (
            "Headroom saved 56.28% of input tokens, up from 55.69%.",
            "add Headroom with --proxy-url http://127.0.0.1:8787",
            "Pilotfish v1.3.10 蒸餾結果; Headroom 另見 runtime guide",
            "reserving GPT-5.6 for judgment; codex routes stay pinned",
        ):
            with self.subTest(line=line):
                self.assertEqual([], module.attributions_in(line))

    def test_a_floor_is_not_a_stale_attestation(self) -> None:
        # `需要 Claude Code 2.1.207 以上版本` differs from the local version for
        # as long as the requirement stands. Reported as a discrepancy it would
        # appear on every run forever, which is how a report teaches people to
        # skip it.
        module = self._module()
        line = "1. `verifier` 需要 Claude Code 2.1.207 以上版本."
        self.assertIn(("claude code", "2.1.207"), module.attributions_in(line))
        self.assertTrue(module.FLOOR.search(line))
        self.assertEqual(
            "floor-met", module.verdict_for("2.1.207", "2.1.226", is_floor=True))
        self.assertEqual(
            "floor-unmet", module.verdict_for("2.1.207", "2.1.99", is_floor=True))

    def test_a_truncated_claim_still_matches_the_release_it_names(self) -> None:
        # Prose writes `headroom 0.34`; the binary answers `0.34.0`. Treating
        # that as a difference would bury the real ones.
        module = self._module()
        self.assertEqual("match", module.verdict_for("0.34", "0.34.0", False))
        self.assertEqual("differs", module.verdict_for("0.33", "0.34.0", False))

    def test_a_zh_tw_floor_and_a_dated_title_are_not_stale_attestations(self) -> None:
        """Two shapes added 2026-08-17, both from the same review of a real report.

        Half of that run's discrepancies were sentences that are still true.
        `起` is zh-TW's "from <version> onwards", the exact counterpart of the
        English floors this class already covers, so `Headroom v0.34 起已移除 …`
        was filed as a permanent finding about a correct sentence. And a dated
        section title names the version it was *about*: rewriting
        `#### 2026-08-10 查核結果 (Headroom 0.34 升級)` to today's number destroys
        the record it exists to keep.

        The dividing line is what the guard below asserts, and it is the one that
        matters: exempting *headings* is not exempting dated lines. A dated claim
        in prose is precisely what this instrument is for - the date is what makes
        going stale checkable - so the exemption is keyed on the heading marker
        and the anchor link, never on the presence of a date.
        """
        module = self._module()
        floor = "Headroom v0.34 起已移除 CLI context tools; wrapper 不再傳入舊參數."
        self.assertIn(("headroom", "0.34"), module.attributions_in(floor))
        self.assertTrue(module.FLOOR.search(floor))
        self.assertEqual(
            "floor-met", module.verdict_for("0.34", "0.35.0", is_floor=True))

        for line in (
            "#### 2026-08-10 查核結果 (Headroom 0.34 升級): 同一個失效換了一層皮",
            "- [2026-08-10 查核結果 (Headroom 0.34 升級)](landing-log.md"
            "#2026-08-10-查核結果-headroom-034-升級)",
        ):
            with self.subTest(line=line[:40]):
                self.assertTrue(module.HISTORY.search(line))

        # The guard. Same date, same tool, same wrong number - still a claim.
        claim = "2026-08-10 本機查核: CLI 與 proxy 都是 `headroom-ai 0.34.0`."
        self.assertIsNone(
            module.HISTORY.search(claim),
            "a dated prose attestation must stay checkable; exempting it would "
            "make the date - the thing that makes staleness detectable - into "
            "the way to avoid being checked")

    def test_it_reports_and_never_fails(self) -> None:
        # Same contract as the rest of this script: a stale attestation is a
        # fact to weigh. Made fail-closed, the cheapest way to stay green would
        # be to stop writing the date next to what was checked.
        finished = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "evidence-check.py"), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(0, finished.returncode, finished.stderr)
        report = json.loads(finished.stdout)
        self.assertIn("versions", report)
        self.assertIn("attestations", report)
        for row in report["versions"]:
            self.assertIn(row["verdict"], {
                "match", "differs", "floor-met", "floor-unmet", "unprobeable"})


if __name__ == '__main__':
    unittest.main()
