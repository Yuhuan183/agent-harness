"""Experience ledger: logging, pending pairing, reporting, revision."""
from support import *  # noqa: F401,F403


class SharedSkillTests(unittest.TestCase):
    def _assert_symlinked_body(self, name: str) -> None:
        body = ROOT / "main/.agents/skills" / name
        self.assertTrue((body / "SKILL.md").is_file(), f"{name} body missing")
        for stub in (f"main/.claude/skills/{name}", f"main/.codex/skills/{name}"):
            link = ROOT / stub
            self.assertTrue(link.is_symlink(), f"{stub} is not a symlink")
            self.assertEqual(os.readlink(link), f"../../.agents/skills/{name}")
            self.assertTrue((link / "SKILL.md").is_file(), f"{stub} does not resolve")

    def test_headroom_protocol_is_shared_via_symlink(self) -> None:
        self._assert_symlinked_body("headroom-protocol")
        skill = read(".agents/skills/headroom-protocol/SKILL.md")
        self.assertIn("headroom doctor", skill)
        self.assertNotIn("/livez", skill)

    def test_speak_human_tw_is_shared_via_symlink(self) -> None:
        self._assert_symlinked_body("speak-human-tw")

    def test_speak_human_tw_layout_and_attribution(self) -> None:
        base = "main/.agents/skills/speak-human-tw"
        for ref in ("patterns", "taiwan-localization", "protected-list", "humanize"):
            self.assertTrue((ROOT / base / "references" / f"{ref}.md").is_file(), ref)
        self.assertTrue((ROOT / base / "agents/openai.yaml").is_file())
        meta = frontmatter(f"{base}/SKILL.md")
        self.assertIn("name: speak-human-tw", meta)
        self.assertNotIn("user-invocable:", meta)
        self.assertIn("license: MIT", meta)
        skill = read(f"{base}/SKILL.md")
        for ref in ("patterns.md", "taiwan-localization.md", "protected-list.md", "humanize.md"):
            self.assertIn(ref, skill)
        self.assertIn("## 選擇工作模式", skill)
        self.assertIn("改寫模式（預設）", skill)
        self.assertNotIn("先列清單、等確認", skill)
        # MIT derivative must carry the upstream notice.
        attribution = read(f"{base}/ATTRIBUTION.md")
        self.assertIn("MIT", attribution)
        self.assertIn("Raymond Hou", attribution)
        self.assertIn("Raymondhou0917/speak-human-tw", attribution)

    def test_shared_skill_names_are_listed(self) -> None:
        installed = read(".agents/skills/INSTALLED.txt").splitlines()
        actual = sorted(
            path.name
            for path in (ROOT / "main/.agents/skills").iterdir()
            if (path / "SKILL.md").is_file()
        )
        self.assertEqual(installed, actual)
        self.assertEqual(
            installed,
            [
                "experience-ledger",
                "headroom-protocol",
                "speak-human-tw",
                "task-observer",
            ],
        )

    def test_experience_ledger_is_shared_and_wired(self) -> None:
        self._assert_symlinked_body("experience-ledger")
        base = ROOT / "main/.agents/skills/experience-ledger"
        for script in ("experience-log", "experience-report", "experience-revise"):
            path = base / "scripts" / script
            self.assertTrue(path.is_file(), script)
            self.assertTrue(os.access(path, os.X_OK), f"{script} not executable")
        self.assertTrue((base / "references/metrics.md").is_file())
        self.assertTrue((base / "agents/openai.yaml").is_file())
        # baton-dispatch owns the post-QC write; provider-routing retains route evidence.
        baton = read(".claude/skills/baton-dispatch/SKILL.md")
        routing = read(".claude/skills/provider-routing/SKILL.md")
        self.assertIn("After QC, load `experience-ledger`", baton)
        self.assertIn("log the same route through `experience-ledger`", routing)

    def test_experience_scripts_log_and_report(self) -> None:
        base = ROOT / "main/.agents/skills/experience-ledger/scripts"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = os.path.join(temp_dir, "experience.jsonl")
            env = {**os.environ, "AGENT_EXPERIENCE_LEDGER": ledger,
                   "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing")}

            def log(*extra: str) -> None:
                subprocess.run(
                    [sys.executable, str(base / "experience-log"), *extra],
                    env=env, check=True, capture_output=True, text=True,
                )

            for i in range(10):
                log("--role", "executor", "--provider", "claude",
                    "--request-source", "claude-code", "--class", "impl",
                    "--outcome", "accepted", "--quality", "4",
                    "--tokens-in", "100", "--tokens-out", "20",
                    "--cache-write-tokens", "10", "--cache-read-tokens", "70",
                    "--secs", "300", "--review-secs", "30", "--rework-secs", "0",
                    "--api-cost-usd", "0.25",
                    "--now", f"2026-07-{19 + i // 8:02d}T{i % 8:02d}:00:00+00:00")
            log("--role", "executor", "--provider", "codex",
                "--request-source", "codex", "--class", "impl",
                "--profile", "balanced", "--model", "gpt-5.6-sol",
                "--effort", "medium",
                "--outcome", "failed", "--now", "2026-07-19T06:00:00+00:00")
            # invalid provider must be rejected
            bad = subprocess.run(
                [sys.executable, str(base / "experience-log"),
                 "--role", "executor", "--provider", "gemini", "--outcome", "accepted"],
                env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(bad.returncode, 0)

            result = subprocess.run(
                [sys.executable, str(base / "experience-report"),
                 "--now", "2026-07-22T00:00:00+00:00", "--json"],
                env=env, check=True, capture_output=True, text=True,
            )
            report = json.loads(result.stdout)
        self.assertEqual(report["records"], 11)
        claude = report["by_cohort_provider"]["executor/impl/claude"]
        codex = report["by_cohort_provider"]["executor/impl/codex"]
        self.assertEqual(claude["AR"], 100.0)
        self.assertEqual(claude["avg_secs"], 300.0)
        self.assertEqual(claude["avg_total_secs"], 330.0)
        self.assertEqual(claude["avg_total_tokens"], 200.0)
        self.assertEqual(claude["avg_api_cost_usd"], 0.25)
        self.assertEqual(claude["request_sources"], {"claude-code": 10})
        self.assertEqual(codex["FR"], 100.0)
        self.assertEqual(codex["request_sources"], {"codex": 1})
        self.assertIn("explore codex", report["hints"]["executor/impl"])

    def test_fallback_lineage_requires_all_three_fields(self) -> None:
        # F-04: origin + parent dispatch id + exactly one hop, together.
        base = ROOT / "main/.agents/skills/experience-ledger/scripts"
        common = ["--role", "executor", "--provider", "codex",
                  "--request-source", "codex", "--class", "impl",
                  "--profile", "balanced", "--model", "gpt-5.6-sol",
                  "--effort", "medium", "--outcome", "accepted"]
        cases = {
            "no parent": ["--origin-provider", "claude", "--fallback-hops", "1"],
            "empty parent": ["--origin-provider", "claude", "--fallback-hops", "1",
                             "--parent-dispatch-id", "  "],
            "no origin": ["--parent-dispatch-id", "s:1", "--fallback-hops", "1"],
            "hops 2": ["--origin-provider", "claude", "--fallback-hops", "2",
                       "--parent-dispatch-id", "s:1"],
            "hops 0": ["--origin-provider", "claude", "--fallback-hops", "0",
                       "--parent-dispatch-id", "s:1"],
            "same provider": ["--origin-provider", "codex", "--fallback-hops", "1",
                              "--parent-dispatch-id", "s:1"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {**os.environ,
                   "AGENT_EXPERIENCE_LEDGER": os.path.join(temp_dir, "l.jsonl"),
                   "AGENT_EXPERIENCE_PENDING": os.path.join(temp_dir, "p.jsonl")}
            for label, extra in cases.items():
                bad = subprocess.run(
                    [sys.executable, str(base / "experience-log"), *common, *extra],
                    env=env, capture_output=True, text=True,
                )
                self.assertNotEqual(bad.returncode, 0, label)
            good = subprocess.run(
                [sys.executable, str(base / "experience-log"), *common,
                 "--origin-provider", "claude", "--fallback-hops", "1",
                 "--parent-dispatch-id", "session:dispatch-1"],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(good.returncode, 0, good.stderr)

    def test_experience_log_keeps_review_separate_from_recon(self) -> None:
        base = ROOT / "main/.agents/skills/experience-ledger/scripts"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = os.path.join(temp_dir, "experience.jsonl")
            env = {**os.environ, "AGENT_EXPERIENCE_LEDGER": ledger,
                   "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing")}
            common = [
                # Legacy capitalized spelling: the alias must canonicalize it.
                "--role", "Explore", "--provider", "claude",
                "--request-source", "claude-code", "--profile", "balanced",
                "--model", "claude-sonnet-5", "--effort", "low",
                "--outcome", "accepted",
            ]
            for task_class in ("recon", "review"):
                subprocess.run(
                    [sys.executable, str(base / "experience-log"), *common,
                     "--class", task_class, "--task", f"{task_class} sample"],
                    env=env, check=True, capture_output=True, text=True,
                )
            result = subprocess.run(
                [sys.executable, str(base / "experience-report"), "--json"],
                env=env, check=True, capture_output=True, text=True,
            )
            report = json.loads(result.stdout)
            records = [json.loads(line) for line in Path(ledger).read_text().splitlines()]
        self.assertEqual(report["by_cohort_provider"]["explore/recon/claude"]["n"], 1)
        self.assertEqual(report["by_cohort_provider"]["explore/review/claude"]["n"], 1)
        self.assertEqual({row["task_class"]: row["tier"] for row in records},
                         {"recon": "spot", "review": "full"})

    def test_experience_pending_pairs_by_session_and_consumes_one_dispatch(self) -> None:
        hook = ROOT / "main/.claude/hooks/experience-pending.py"
        log_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-log"
        with tempfile.TemporaryDirectory() as temp_dir:
            pending = Path(temp_dir) / "pending.jsonl"
            ledger = Path(temp_dir) / "experience.jsonl"
            now = datetime.now(timezone.utc)
            records = [
                {"ts": (now - timedelta(seconds=100)).isoformat(),
                 "event": "SubagentStart", "agent_type": "executor",
                 "agent_id": "shared", "session_id": "session-b"},
                {"ts": (now - timedelta(seconds=1)).isoformat(),
                 "event": "SubagentStart", "agent_type": "executor",
                 "agent_id": "shared", "session_id": "session-a"},
            ]
            pending.write_text(
                "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8"
            )
            transcript_base = Path(temp_dir) / "transcript"
            transcript = transcript_base / "subagents" / "agent-shared.jsonl"
            transcript.parent.mkdir(parents=True)
            transcript.write_text(json.dumps({"message": {
                "id": "m1", "usage": {
                    "input_tokens": 100, "output_tokens": 20,
                    "cache_creation_input_tokens": 10,
                    "cache_read_input_tokens": 70,
                }
            }}) + "\n", encoding="utf-8")
            env = {
                **os.environ,
                "AGENT_EXPERIENCE_PENDING": str(pending),
                "AGENT_EXPERIENCE_LEDGER": str(ledger),
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing"),
            }
            before_system_spawn = pending.read_text()
            subprocess.run(
                [sys.executable, str(hook)], env=env,
                input=json.dumps({
                    "hook_event_name": "SubagentStop", "agent_type": "",
                    "agent_id": "system", "session_id": "session-system",
                }),
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(pending.read_text(), before_system_spawn)
            stop = {
                "hook_event_name": "SubagentStop",
                "agent_type": "executor",
                "agent_id": "shared",
                "session_id": "session-b",
                "transcript_path": str(transcript_base) + ".jsonl",
            }
            subprocess.run(
                [sys.executable, str(hook)], env=env, input=json.dumps(stop),
                check=True, capture_output=True, text=True,
            )
            staged = [json.loads(line) for line in pending.read_text().splitlines()]
            self.assertGreater(staged[-1]["secs"], 90)
            self.assertLess(staged[-1]["secs"], 120)

            subprocess.run(
                [sys.executable, str(log_script), "--from-pending",
                 "--outcome", "accepted"],
                env=env, check=True, capture_output=True, text=True,
            )
            logged = json.loads(ledger.read_text().strip())
            self.assertEqual(logged["session"], "session-b")
            self.assertEqual(logged["schema"], 3)
            self.assertEqual(logged["request_source"], "claude-code")
            self.assertEqual(logged["dispatch_id"], "session-b:shared")
            self.assertEqual(logged["token_scope"], "full")
            self.assertEqual(logged["tokens_in"], 100)
            self.assertEqual(logged["tokens_out"], 20)
            self.assertEqual(logged["cache_write_tokens"], 10)
            self.assertEqual(logged["cache_read_tokens"], 70)
            remaining = [json.loads(line) for line in pending.read_text().splitlines()]
            self.assertEqual(len(remaining), 1)
            self.assertEqual(remaining[0]["session_id"], "session-a")

    def test_experience_log_requires_dispatch_id_for_overlapping_completions(self) -> None:
        log_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-log"
        with tempfile.TemporaryDirectory() as temp_dir:
            pending = Path(temp_dir) / "pending.jsonl"
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = []
            for suffix in ("a", "b"):
                common = {
                    "agent_type": "executor", "agent_id": suffix,
                    "session_id": "session", "request_source": "claude-code",
                    "dispatch_id": f"session:{suffix}",
                }
                rows.append({**common, "event": "SubagentStart"})
                rows.append({**common, "event": "SubagentStop", "secs": 1.0})
            pending.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            env = {
                **os.environ,
                "AGENT_EXPERIENCE_PENDING": str(pending),
                "AGENT_EXPERIENCE_LEDGER": str(ledger),
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing"),
            }
            ambiguous = subprocess.run(
                [sys.executable, str(log_script), "--from-pending",
                 "--outcome", "accepted"],
                env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(ambiguous.returncode, 0)
            self.assertIn("multiple completed dispatches", ambiguous.stderr)
            self.assertFalse(ledger.exists())

            selected = subprocess.run(
                [sys.executable, str(log_script), "--from-pending",
                 "--dispatch-id", "session:b", "--outcome", "accepted"],
                env=env, check=True, capture_output=True, text=True,
            )
            self.assertIn("logged", selected.stdout)
            logged = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual(logged["dispatch_id"], "session:b")
            self.assertEqual(logged["request_source"], "claude-code")

    def test_invalid_bridge_log_does_not_consume_pending_completion(self) -> None:
        log_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-log"
        with tempfile.TemporaryDirectory() as temp_dir:
            pending = Path(temp_dir) / "pending.jsonl"
            ledger = Path(temp_dir) / "experience.jsonl"
            common = {
                "agent_type": "codex:codex-rescue", "agent_id": "bridge",
                "session_id": "session", "request_source": "claude-code-plugin-codex",
                "dispatch_id": "session:bridge",
            }
            pending.write_text(
                json.dumps({**common, "event": "SubagentStart"}) + "\n"
                + json.dumps({**common, "event": "SubagentStop", "secs": 2.0}) + "\n",
                encoding="utf-8",
            )
            before = pending.read_text(encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(log_script), "--from-pending",
                 "--dispatch-id", "session:bridge", "--role", "executor",
                 "--outcome", "accepted"],
                env={**os.environ, "AGENT_EXPERIENCE_PENDING": str(pending),
                     "AGENT_EXPERIENCE_LEDGER": str(ledger),
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing")},
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("production records require a resolved route", result.stderr)
            self.assertEqual(pending.read_text(encoding="utf-8"), before)
            self.assertFalse(ledger.exists())

    def test_experience_report_never_mixes_total_and_output_only_cost(self) -> None:
        report_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-report"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = []
            for provider, source in (("claude", "claude-code"), ("codex", "codex")):
                for i in range(10):
                    row = {
                        "ts": f"2026-07-20T{i:02d}:00:00+00:00",
                        "schema": 3, "role": "executor", "task_class": "impl",
                        "provider": provider, "request_source": source,
                        "outcome": "accepted", "tokens_out": 20,
                        "profile": "balanced",
                        "model": ("claude-opus-4-8" if provider == "claude"
                                  else "gpt-5.6-sol"),
                        "effort": "medium",
                    }
                    if provider == "claude":
                        row.update({"tokens_in": 100, "cache_write_tokens": 10,
                                    "cache_read_tokens": 70, "token_scope": "full"})
                    else:
                        row["token_scope"] = "output_only"
                    rows.append(row)
            ledger.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(report_script), "--json",
                 "--now", "2026-07-22T00:00:00+00:00"],
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger),
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing")},
                check=True, capture_output=True, text=True,
            )
        report = json.loads(result.stdout)
        self.assertIn("no comparable cost scope", report["hints"]["executor/impl"])
        self.assertEqual(
            report["by_cohort_provider"]["executor/impl/claude"]["coverage"]
            ["total_tokens"], 10,
        )
        self.assertEqual(
            report["by_cohort_provider"]["executor/impl/codex"]["coverage"]
            ["total_tokens"], 0,
        )

    def test_experience_report_does_not_pool_routes_to_reach_sample_floor(self) -> None:
        report_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-report"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = []
            routes = {
                "claude": (
                    "claude-code",
                    (("balanced", "claude-sonnet-5", "high"),
                     ("fast", "claude-opus-4-8", "low")),
                ),
                "codex": (
                    "codex",
                    (("balanced", "gpt-5.6-sol", "medium"),
                     ("fast", "gpt-5.6-sol", "low")),
                ),
            }
            for provider, (source, provider_routes) in routes.items():
                for profile, model, effort in provider_routes:
                    for i in range(5):
                        rows.append({
                            "ts": f"2026-07-20T{i:02d}:00:00+00:00",
                            "schema": 3, "role": "executor",
                            "task_class": "impl", "provider": provider,
                            "request_source": source, "outcome": "accepted",
                            "profile": profile, "model": model, "effort": effort,
                        })
            ledger.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(report_script), "--json",
                 "--now", "2026-07-22T00:00:00+00:00"],
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger),
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing")},
                check=True, capture_output=True, text=True,
            )
        report = json.loads(result.stdout)
        self.assertEqual(
            report["by_cohort_provider"]["executor/impl/claude"]["n"], 10
        )
        self.assertEqual(
            report["by_cohort_provider"]["executor/impl/codex"]["n"], 10
        )
        self.assertEqual(
            report["by_route_cohort_provider"]
            ["executor/impl/claude/balanced/claude-sonnet-5/high"]["n"], 5
        )
        self.assertEqual(
            report["by_route_cohort_provider"]
            ["executor/impl/codex/balanced/gpt-5.6-sol/medium"]["n"], 5
        )
        self.assertIn("explore claude, codex", report["hints"]["executor/impl"])

    def test_experience_report_excludes_smoke_and_other_from_decision_counts(self) -> None:
        report_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-report"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = []
            for task_class in ("smoke", "other"):
                rows.append({
                    "ts": "2026-07-20T00:00:00+00:00", "schema": 3,
                    "role": "executor", "task_class": task_class,
                    "provider": "codex", "request_source": "codex",
                    "outcome": "accepted", "profile": "balanced",
                    "model": "gpt-5.6-sol", "effort": "medium",
                })
            ledger.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(report_script), "--json",
                 "--now", "2026-07-22T00:00:00+00:00"],
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger),
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing")},
                check=True, capture_output=True, text=True,
            )
        report = json.loads(result.stdout)
        self.assertEqual(report["decision_records"], 0)
        self.assertEqual(report["hints"], {})
        for task_class in ("smoke", "other"):
            row = report["by_cohort_provider"][f"executor/{task_class}/codex"]
            self.assertEqual(row["observed_n"], 1)
            self.assertEqual(row["ineligible_n"], 1)
            self.assertEqual(row["n"], 0)

    def test_experience_report_ignores_invalid_legacy_telemetry(self) -> None:
        report_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-report"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "experience.jsonl"
            valid = {
                "ts": "2026-07-20T00:00:00+00:00", "schema": 3,
                "role": "executor", "task_class": "impl",
                "provider": "codex", "request_source": "codex",
                "outcome": "accepted", "profile": "balanced",
                "model": "gpt-5.6-sol", "effort": "medium",
                "quality": 4, "tokens_in": 100, "tokens_out": 20,
                "cache_write_tokens": 10, "cache_read_tokens": 70,
                "secs": 5.0, "review_secs": 1.0, "rework_secs": 0.0,
                "api_cost_usd": 0.25,
            }
            invalid = {
                **valid, "ts": "2026-07-20T01:00:00+00:00",
                "quality": 99, "tokens_in": -1, "tokens_out": -20,
                "cache_write_tokens": 10, "cache_read_tokens": 70,
                "secs": float("nan"), "review_secs": 1.0, "rework_secs": 0.0,
                "api_cost_usd": float("inf"),
            }
            ledger.write_text(
                json.dumps(valid) + "\n" + json.dumps(invalid) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(report_script), "--json",
                 "--now", "2026-07-22T00:00:00+00:00"],
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger)},
                check=True, capture_output=True, text=True,
            )
        row = json.loads(result.stdout)["by_cohort_provider"]["executor/impl/codex"]
        self.assertEqual(row["n"], 2)
        self.assertEqual(row["QS"], 4.0)
        self.assertEqual(row["avg_tokens_out"], 20.0)
        self.assertEqual(row["avg_total_tokens"], 200.0)
        self.assertEqual(row["avg_secs"], 5.0)
        self.assertEqual(row["avg_total_secs"], 6.0)
        self.assertEqual(row["avg_api_cost_usd"], 0.25)
        self.assertEqual(row["coverage"], {
            "tokens_out": 1, "total_tokens": 1, "secs": 1,
            "total_secs": 1, "api_cost_usd": 1,
        })

    def test_experience_report_renders_all_legacy_cohorts(self) -> None:
        report_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-report"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = [
                {
                    "ts": "2026-07-20T00:00:00+00:00", "schema": 2,
                    "role": "Explore", "task_class": "recon",
                    "provider": "claude", "outcome": "accepted",
                    "model": "claude-sonnet-5", "effort": "low",
                },
                {
                    "ts": "2026-07-20T01:00:00+00:00", "schema": 1,
                    "role": "mech-executor", "task_class": "impl",
                    "provider": "codex", "outcome": "failed",
                },
            ]
            ledger.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(report_script),
                 "--now", "2026-07-22T00:00:00+00:00"],
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger),
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/.claude/scripts/model-routing")},
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        # Legacy schema-2 rows spell the role "Explore"; the report renders the
        # canonical lowercase cohort.
        self.assertIn("explore", result.stdout)
        self.assertIn("mech-executor", result.stdout)
        self.assertIn("legacy-unknown", result.stdout)
        self.assertNotIn("TypeError", result.stderr)



if __name__ == '__main__':
    unittest.main()
