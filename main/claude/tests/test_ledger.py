"""Experience ledger: logging, pending pairing, reporting, revision."""
import fcntl

from support import *  # noqa: F401,F403


def _decision_route_sources() -> tuple[str, ...]:
    """The live eligibility gate, so a tag and its consequence stay tied.

    Asserting the tier name alone would still pass if the tier stopped being
    decision-eligible. `test_report_and_revise_share_one_eligibility_rule` pins
    the tuple's contents; these read it.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "routing_core_for_ledger_tests",
        ROOT / "main/.agents/scripts/routing_core.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DECISION_ROUTE_SOURCES


DECISION_ROUTE_SOURCES = _decision_route_sources()


def stage_attested_stop(pending, dispatch_id: str, *, agent_type: str,
                        observed_model: str, **extra) -> None:
    """Append the SubagentStop stub the pending hook stages for a Claude run.

    Route provenance has no CLI flag by design — it may only arrive from the
    provider's own telemetry — so anything that needs a decision-eligible
    record has to come through the pending file, as a real dispatch does.
    """
    session, _, agent = dispatch_id.partition(":")
    with open(pending, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": "SubagentStop", "agent_type": agent_type,
            "agent_id": agent, "session_id": session,
            "dispatch_id": dispatch_id, "request_source": "claude-code",
            "observed_model": observed_model, **extra,
        }) + "\n")


class SharedSkillTests(unittest.TestCase):
    def _assert_symlinked_body(self, name: str) -> None:
        body = ROOT / "main/.agents/skills" / name
        self.assertTrue((body / "SKILL.md").is_file(), f"{name} body missing")
        for stub in (f"main/claude/skills/{name}", f"main/codex/skills/{name}"):
            link = ROOT / stub
            self.assertTrue(link.is_symlink(), f"{stub} is not a symlink")
            self.assertEqual(os.readlink(link), f"../../.agents/skills/{name}")
            self.assertTrue((link / "SKILL.md").is_file(), f"{stub} does not resolve")

    def test_headroom_protocol_is_shared_with_explicit_auto_invocation(self) -> None:
        shared = ROOT / "main/.agents/skills/headroom-protocol"
        claude = ROOT / "main/claude/skills/headroom-protocol"
        codex = ROOT / "main/codex/skills/headroom-protocol"
        self.assertTrue((shared / "SKILL.md").is_file())
        self.assertTrue(claude.is_dir())
        self.assertFalse(claude.is_symlink())
        claude_skill = (claude / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("disable-model-invocation: false", claude_skill)
        claude_meta = frontmatter("main/claude/skills/headroom-protocol/SKILL.md")
        shared_meta = frontmatter("main/.agents/skills/headroom-protocol/SKILL.md")
        claude_portable_meta = "\n".join(
            line for line in claude_meta.splitlines()
            if not line.startswith("disable-model-invocation:")
        )
        self.assertEqual(claude_portable_meta.rstrip(), shared_meta.rstrip())
        shared_link = claude / "shared-instructions.md"
        self.assertTrue(shared_link.is_symlink())
        self.assertEqual(
            os.readlink(shared_link),
            "../../../.agents/skills/headroom-protocol/SKILL.md",
        )
        self.assertTrue(shared_link.is_file())
        self.assertTrue(codex.is_symlink())
        self.assertEqual(
            os.readlink(codex), "../../.agents/skills/headroom-protocol"
        )
        skill = read(".agents/skills/headroom-protocol/SKILL.md")
        self.assertIn("selected automatically or explicitly", skill)
        self.assertIn("headroom doctor", skill)
        self.assertNotIn("/livez", skill)
        openai = read(".agents/skills/headroom-protocol/agents/openai.yaml")
        self.assertIn("allow_implicit_invocation: true", openai)

    def test_claude_wrapper_replaces_legacy_symlink_without_mutating_shared_skill(
        self,
    ) -> None:
        source = ROOT / "main/claude/skills/headroom-protocol"
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            shared = home / ".agents/skills/headroom-protocol"
            shared.mkdir(parents=True)
            shared_skill = shared / "SKILL.md"
            shared_skill.write_text("legacy shared copy\n", encoding="utf-8")
            target = home / ".claude/skills/headroom-protocol"
            target.parent.mkdir(parents=True)
            target.symlink_to("../../.agents/skills/headroom-protocol")
            result = subprocess.run(
                ["rsync", "-a", "--links", "--force", "--delete",
                 str(source), str(target.parent) + "/"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(target.is_dir())
            self.assertFalse(target.is_symlink())
            self.assertIn(
                "disable-model-invocation: false",
                (target / "SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                shared_skill.read_text(encoding="utf-8"),
                "legacy shared copy\n",
            )

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

    def test_native_claude_route_is_resolver_assumed(self) -> None:
        """The convenience path still logs; it just cannot vote on routes.

        Omitting `--profile/--model/--effort` for a native Claude dispatch is
        documented and supported: the resolver fills the route so the record
        stays readable. But it is filled from the pins as they are *now*, from
        aliases that may since have moved, so it is tagged `resolver-assumed`
        and stays out of the decision set (user-directed 2026-07-28).
        """
    def test_a_dispatch_id_that_ties_to_nothing_says_so(self) -> None:
        """An id the explicit-flags path invents is logged, and used to look
        like a clean success.

        Two replay runs did exactly that on 2026-08-13 — one filed the agent id
        without its session prefix, one filed `rv-policy-01` — and both printed
        `logged: ... -> accepted` with nothing else. The record reconciles no
        stub, which criterion 3 then reports as an un-reconciled dispatch in a
        session that believed it had logged. Not made an error: a Codex
        dispatch or a hook-less run legitimately has no stub. It is the
        silence about the difference that was the defect."""
        base = ROOT / "main/.agents/skills/experience-ledger/scripts"
        common = ["--role", "explore", "--provider", "claude",
                  "--request-source", "claude-code", "--class", "recon",
                  "--outcome", "accepted", "--task", "probe"]

        with tempfile.TemporaryDirectory() as temp_dir:
            pending = Path(temp_dir) / "pending.jsonl"
            session = "11111111-2222-3333-4444-555555555555"
            agent = "a1234567890abcdef"
            staged = f"{session}:{agent}"
            pending.write_text("".join(json.dumps(row) + "\n" for row in (
                {"ts": "2026-08-13T00:00:00+00:00", "event": "SubagentStart",
                 "agent_type": "explore", "agent_id": agent,
                 "session_id": session, "dispatch_id": staged,
                 "request_source": "claude-code"},
                {"ts": "2026-08-13T00:00:05+00:00", "event": "SubagentStop",
                 "agent_type": "explore", "agent_id": agent,
                 "session_id": session, "dispatch_id": staged,
                 "request_source": "claude-code", "secs": 5.0},
            )), encoding="utf-8")
            env = {**os.environ,
                   "AGENT_EXPERIENCE_LEDGER": os.path.join(temp_dir, "l.jsonl"),
                   "AGENT_EXPERIENCE_PENDING": str(pending)}

            invented = subprocess.run(
                [sys.executable, str(base / "experience-log"),
                 "--dispatch-id", "rv-policy-01", *common],
                env=env, check=True, capture_output=True, text=True)
            self.assertIn("matched no staged stub", invented.stdout)
            self.assertIn("`<session_id>:<agent_id>`", invented.stdout)

            real = subprocess.run(
                [sys.executable, str(base / "experience-log"),
                 "--from-pending", "--dispatch-id", staged,
                 "--outcome", "accepted", "--class", "recon"],
                env=env, check=True, capture_output=True, text=True)
            self.assertNotIn("matched no staged stub", real.stdout,
                             "a reconciled log must not carry the warning")

        base = ROOT / "main/.agents/skills/experience-ledger/scripts"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = os.path.join(temp_dir, "experience.jsonl")
            env = {**os.environ, "AGENT_EXPERIENCE_LEDGER": ledger,
                   "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing")}
            subprocess.run(
                [sys.executable, str(base / "experience-log"),
                 "--role", "executor", "--provider", "claude",
                 "--request-source", "claude-code", "--class", "impl",
                 "--outcome", "accepted",
                 "--now", "2026-07-20T00:00:00+00:00"],
                env=env, check=True, capture_output=True, text=True,
            )
            record = json.loads(Path(ledger).read_text(encoding="utf-8").strip())
            # The route is present and usable...
            self.assertEqual(record["route_source"], "resolver-assumed")
            for field in ("profile", "model", "effort"):
                self.assertTrue(record[field], field)
            # ...and still does not reach the decision set.
            result = subprocess.run(
                [sys.executable, str(base / "experience-report"), "--json",
                 "--now", "2026-07-22T00:00:00+00:00"],
                env=env, check=True, capture_output=True, text=True,
            )
        report = json.loads(result.stdout)
        cohort = report["by_cohort_provider"]["executor/impl/claude"]
        self.assertEqual(cohort["observed_n"], 1)
        self.assertEqual(cohort["ineligible_n"], 1)
        self.assertEqual(cohort["n"], 0)
        self.assertEqual(report["decision_records"], 0)

    def test_experience_scripts_log_and_report(self) -> None:
        base = ROOT / "main/.agents/skills/experience-ledger/scripts"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = os.path.join(temp_dir, "experience.jsonl")
            env = {**os.environ, "AGENT_EXPERIENCE_LEDGER": ledger,
                   "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing")}

            def log(*extra: str) -> None:
                subprocess.run(
                    [sys.executable, str(base / "experience-log"), *extra],
                    env=env, check=True, capture_output=True, text=True,
                )

            # Cohort metrics are computed from decision-eligible records only,
            # so each dispatch is staged with the model its transcript recorded
            # — a route typed on the command line is a claim and would leave
            # every metric below None, asserting nothing.
            # `test_native_claude_route_is_resolver_assumed` covers the
            # convenience path, where nothing is staged and nothing is claimed.
            pending = Path(temp_dir) / "pending.jsonl"
            env["AGENT_EXPERIENCE_PENDING"] = str(pending)
            for i in range(10):
                stage_attested_stop(pending, f"s:a{i}", agent_type="executor",
                                    observed_model="claude-opus-5")
                log("--from-pending", "--dispatch-id", f"s:a{i}",
                    "--role", "executor", "--provider", "claude",
                    "--request-source", "claude-code", "--class", "impl",
                    "--profile", "balanced", "--model", "claude-opus-5",
                    "--effort", "medium",
                    "--outcome", "accepted", "--quality", "4",
                    "--tokens-in", "100", "--tokens-out", "20",
                    "--cache-write-tokens", "10", "--cache-read-tokens", "70",
                    "--secs", "300", "--review-secs", "30", "--rework-secs", "0",
                    "--api-cost-usd", "0.25",
                    "--now", f"2026-07-{19 + i // 8:02d}T{i % 8:02d}:00:00+00:00")
            stage_attested_stop(pending, "s:c0", agent_type="codex:codex-rescue",
                                observed_model="gpt-5.6-sol",
                                observed_effort="medium",
                                request_source="codex")
            log("--from-pending", "--dispatch-id", "s:c0",
                "--role", "executor", "--provider", "codex",
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
                   "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing")}
            pending = Path(temp_dir) / "pending.jsonl"
            env["AGENT_EXPERIENCE_PENDING"] = str(pending)
            common = [
                # Legacy capitalized spelling: the alias must canonicalize it.
                "--role", "Explore", "--provider", "claude",
                "--request-source", "claude-code", "--profile", "balanced",
                "--model", "claude-sonnet-5", "--effort", "low",
                "--outcome", "accepted",
            ]
            for task_class in ("recon", "review"):
                # Cohort counts below are of decision-eligible records, so the
                # route has to be attested by the transcript rather than
                # claimed on the command line.
                stage_attested_stop(pending, f"s:{task_class}",
                                    agent_type="explore",
                                    observed_model="claude-sonnet-5")
                subprocess.run(
                    [sys.executable, str(base / "experience-log"), *common,
                     "--from-pending", "--dispatch-id", f"s:{task_class}",
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
        # Both cohorts sit under the comparable-n threshold, so their hints say
        # "collect more", not "route differently". weekly-integrity reads this
        # key to keep a hint that can never clear out of its findings.
        self.assertEqual(sorted(report["hints_insufficient"]),
                         ["explore/recon", "explore/review"])
        self.assertEqual(sorted(report["hints"]), sorted(report["hints_insufficient"]))
        self.assertEqual({row["task_class"]: row["tier"] for row in records},
                         {"recon": "spot", "review": "full"})

    def test_experience_pending_pairs_by_session_and_consumes_one_dispatch(self) -> None:
        hook = ROOT / "main/claude/hooks/experience-pending.py"
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
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing"),
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
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing"),
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
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing")},
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("production records require a resolved route", result.stderr)
            self.assertEqual(pending.read_text(encoding="utf-8"), before)
            self.assertFalse(ledger.exists())

    def test_explicit_logging_clears_its_own_pending_stub(self) -> None:
        """Logging with explicit flags must consume the stub it accounts for.

        The hook stages a stub per dispatch, not per logging style. Only
        `--from-pending` used to clear it, so every dispatch logged with
        explicit flags — the required form for bridge and native-Codex
        records — left its start/stop pair behind and the pending file grew by
        two rows per dispatch with nothing ever removing them.
        """
        log_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-log"
        with tempfile.TemporaryDirectory() as temp_dir:
            pending = Path(temp_dir) / "pending.jsonl"
            ledger = Path(temp_dir) / "experience.jsonl"
            rows = []
            for suffix in ("a", "b"):
                common = {
                    "ts": "2026-07-20T00:00:00+00:00",
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
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing"),
            }
            explicit = [
                sys.executable, str(log_script), "--outcome", "accepted",
                "--role", "executor", "--provider", "claude",
                "--request-source", "claude-code", "--profile", "balanced",
                "--model", "claude-sonnet-5", "--effort", "low",
            ]
            subprocess.run(explicit + ["--dispatch-id", "session:a"],
                           env=env, check=True, capture_output=True, text=True)
            # Only the named dispatch is reconciled; a concurrent one is not.
            remaining = [json.loads(line) for line
                         in pending.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["dispatch_id"] for row in remaining],
                             ["session:b", "session:b"])

            subprocess.run(explicit + ["--dispatch-id", "session:b"],
                           env=env, check=True, capture_output=True, text=True)
            self.assertEqual(pending.read_text(encoding="utf-8"), "")
            logged = [json.loads(line) for line
                      in ledger.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["dispatch_id"] for row in logged],
                             ["session:a", "session:b"])

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
                        "model": ("claude-opus-5" if provider == "claude"
                                  else "gpt-5.6-sol"),
                        "effort": "medium",
                        # Attested route: this fixture is about cost scope, so
                        # it must clear the provenance gate to reach the hint.
                        "route_source": ("rollout-verified" if provider == "codex"
                                         else "transcript-verified"),
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
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing")},
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
                     ("fast", "claude-opus-5", "low")),
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
                            # This fixture is about route pooling, not
                            # provenance; keep every row decision-eligible.
                            "route_source": ("rollout-verified" if provider == "codex"
                                             else "transcript-verified"),
                        })
            ledger.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(report_script), "--json",
                 "--now", "2026-07-22T00:00:00+00:00"],
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger),
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing")},
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
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing")},
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

    def test_unattested_routes_are_reported_but_never_drive_decisions(self) -> None:
        # Only what the provider itself recorded may move a route.
        # `resolver-assumed` is inferred from an alias and stops being true the
        # moment that alias is upgraded; `explicit` is the dispatcher's own
        # claim with nothing checking it against what ran; an untagged record
        # has no provenance at all. All stay visible in observed_n/ineligible_n
        # — the gate is on driving a decision, not on being counted.
        report_script = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-report"
        base = {
            "ts": "2026-07-20T00:00:00+00:00", "schema": 3,
            "role": "executor", "task_class": "impl",
            "provider": "codex", "request_source": "codex",
            "outcome": "accepted", "profile": "balanced",
            "model": "gpt-5.6-sol", "effort": "medium",
        }
        cases = {
            "rollout-verified": 1,
            "transcript-verified": 1,
            "explicit": 0,
            "resolver-assumed": 0,
            None: 0,
        }
        for route_source, expected_n in cases.items():
            with self.subTest(route_source=route_source):
                row = dict(base)
                if route_source is not None:
                    row["route_source"] = route_source
                with tempfile.TemporaryDirectory() as temp_dir:
                    ledger = Path(temp_dir) / "experience.jsonl"
                    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(report_script), "--json",
                         "--now", "2026-07-22T00:00:00+00:00"],
                        env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger),
                             "AGENT_CLAUDE_RESOLVER": str(
                                 ROOT / "main/claude/scripts/model-routing")},
                        check=True, capture_output=True, text=True,
                    )
                report = json.loads(result.stdout)
                cohort = report["by_cohort_provider"]["executor/impl/codex"]
                self.assertEqual(cohort["observed_n"], 1)
                self.assertEqual(cohort["n"], expected_n)
                self.assertEqual(cohort["ineligible_n"], 1 - expected_n)
                self.assertEqual(report["decision_records"], expected_n)

    def test_report_and_revise_share_one_eligibility_rule(self) -> None:
        # Two surfaces read the same ledger: one reports the evidence, the
        # other proposes route changes from it. If their filters drift, a
        # record can be excluded from the report a human reads while still
        # moving a route, which is the failure worth gating.
        skills = ROOT / "main/.agents/skills/experience-ledger/scripts"
        report = (skills / "experience-report").read_text(encoding="utf-8")
        revise = (skills / "experience-revise").read_text(encoding="utf-8")
        for source in (report, revise):
            self.assertIn("core.DECISION_ROUTE_SOURCES", source)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "routing_core_eligibility", ROOT / "main/.agents/scripts/routing_core.py")
        routing_core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(routing_core)
        # Both entries are provider-attested; a dispatcher's own claim
        # (`explicit`) is deliberately not one of them.
        self.assertEqual(
            routing_core.DECISION_ROUTE_SOURCES,
            ("rollout-verified", "transcript-verified"))

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
                "route_source": "rollout-verified",
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
               "AGENT_CLAUDE_RESOLVER": str(ROOT / "main/claude/scripts/model-routing")},
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        # Legacy schema-2 rows spell the role "Explore"; the report renders the
        # canonical lowercase cohort.
        self.assertIn("explore", result.stdout)
        self.assertIn("mech-executor", result.stdout)
        self.assertIn("legacy-unknown", result.stdout)
        self.assertNotIn("TypeError", result.stderr)


class BridgeRouteEvidenceTests(unittest.TestCase):
    """A bridge record's route must be provider-recorded, not self-reported.

    The bridge job sidecar stores no model or effort, so the dispatcher used to
    hand-type both and the record was tagged `explicit` — a word about how the
    value arrived, not how well it is attested. Codex writes the applied thread
    settings into its own rollout; these tests hold that evidence path open.
    """

    HOOK = ROOT / "main/claude/hooks/experience-pending.py"
    LOG = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-log"

    def _stage(self, temp: Path, rollouts: list[dict]) -> dict:
        """Run the hook over a synthetic bridge dispatch; return its stub."""
        now = datetime.now(timezone.utc)
        sessions = temp / "sessions" / "2026" / "07" / "26"
        sessions.mkdir(parents=True)
        for index, spec in enumerate(rollouts):
            rows = [{
                "timestamp": (now - timedelta(seconds=20)).isoformat().replace(
                    "+00:00", "Z"),
                "type": "event_msg",
                "payload": {"type": "token_count", "info": {"total_token_usage": {
                    "input_tokens": 1000, "cached_input_tokens": 600,
                    "output_tokens": 200}}},
            }]
            if spec:
                rows.insert(0, {
                    "timestamp": (now - timedelta(seconds=30)).isoformat().replace(
                        "+00:00", "Z"),
                    "type": "event_msg",
                    "payload": {"type": "thread_settings_applied",
                                "thread_settings": spec},
                })
            (sessions / f"rollout-probe-{index}.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        pending = temp / "pending.jsonl"
        pending.write_text(json.dumps({
            "ts": (now - timedelta(seconds=60)).isoformat(timespec="seconds"),
            "event": "SubagentStart", "agent_type": "codex:codex-rescue",
            "agent_id": "a1", "session_id": "s1", "dispatch_id": "s1:a1",
            "request_source": "claude-code-plugin-codex",
        }) + "\n", encoding="utf-8")
        self.env = {**os.environ,
                    "AGENT_EXPERIENCE_PENDING": str(pending),
                    "CODEX_SESSIONS_DIR": str(temp / "sessions"),
                    "AGENT_EXPERIENCE_LEDGER": str(temp / "ledger.jsonl")}
        subprocess.run(
            [sys.executable, str(self.HOOK)], env=self.env, check=True,
            capture_output=True, text=True,
            input=json.dumps({"hook_event_name": "SubagentStop",
                              "agent_type": "codex:codex-rescue",
                              "agent_id": "a1", "session_id": "s1"}))
        stubs = [json.loads(line) for line in
                 pending.read_text(encoding="utf-8").splitlines()]
        return stubs[-1]

    def _log(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.LOG), "--from-pending", "--role", "verifier",
             "--outcome", "accepted", "--class", "review",
             "--profile", "quality_guarded", *extra],
            env=self.env, capture_output=True, text=True)

    def test_hook_stages_the_route_codex_actually_ran(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stub = self._stage(Path(temp_dir), [
                {"model": "gpt-5.6-sol", "reasoning_effort": "high"}])
            self.assertEqual(stub["observed_model"], "gpt-5.6-sol")
            self.assertEqual(stub["observed_effort"], "high")
            self.assertEqual(stub["rollout_id"], "rollout-probe-0")

    def test_unclaimed_route_is_filled_from_evidence_and_tagged_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            self._stage(temp, [{"model": "gpt-5.6-sol", "reasoning_effort": "high"}])
            result = self._log()
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(
                (temp / "ledger.jsonl").read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(record["model"], "gpt-5.6-sol")
            self.assertEqual(record["effort"], "high")
            self.assertEqual(record["route_source"], "rollout-verified")

    def test_a_claimed_route_the_provider_did_not_run_is_rejected(self) -> None:
        for flag, value in (("--model", "gpt-5.6-luna"), ("--effort", "low")):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as temp_dir:
                self._stage(Path(temp_dir),
                            [{"model": "gpt-5.6-sol", "reasoning_effort": "high"}])
                result = self._log(flag, value)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("contradicts the provider-recorded route",
                              result.stderr)

    def test_an_unattestable_dispatch_claims_no_route(self) -> None:
        """Two candidate rollouts, or a rollout with no settings, attest nothing.

        Silence is the correct answer here: a window that cannot be pinned to
        one rollout must not lend its route to the record.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            ambiguous = self._stage(Path(temp_dir), [
                {"model": "gpt-5.6-sol", "reasoning_effort": "high"},
                {"model": "gpt-5.6-luna", "reasoning_effort": "low"}])
            self.assertNotIn("observed_model", ambiguous)
            self.assertEqual(ambiguous["telemetry_warning"], "ambiguous_codex_rollout")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            self.assertNotIn("observed_model", self._stage(temp, [None]))
            result = self._log("--model", "gpt-5.6-sol", "--effort", "high")
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(
                (temp / "ledger.jsonl").read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(record["route_source"], "explicit")
            # And a claim nothing checked may not move a route (F-03).
            self.assertNotIn(record["route_source"], DECISION_ROUTE_SOURCES)


class ClaudeRouteEvidenceTests(unittest.TestCase):
    """A Claude route must be attested by Claude, not by the dispatcher.

    `explicit` used to be decision-eligible because Claude had no attestation
    path at all, which made every gate on the Codex side pointless here: a
    dispatcher that typed a route it did not get moved every later route toward
    a model that never ran. Claude records the model on each assistant turn of
    the subagent transcript, which is the same class of evidence as a Codex
    rollout — these tests hold that path open.
    """

    HOOK = ROOT / "main/claude/hooks/experience-pending.py"
    LOG = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-log"

    def _stage(self, temp: Path, models: list[str | None]) -> dict:
        """Run the hook over a synthetic Claude dispatch; return its stub."""
        now = datetime.now(timezone.utc)
        transcript = temp / "session.jsonl"
        subagents = temp / "session" / "subagents"
        subagents.mkdir(parents=True)
        rows = []
        for index, model in enumerate(models):
            message = {"id": f"msg_{index}", "role": "assistant",
                       "usage": {"input_tokens": 100, "output_tokens": 20}}
            if model is not None:
                message["model"] = model
            rows.append({"type": "assistant", "message": message})
        (subagents / "agent-a1.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        pending = temp / "pending.jsonl"
        pending.write_text(json.dumps({
            "ts": (now - timedelta(seconds=60)).isoformat(timespec="seconds"),
            "event": "SubagentStart", "agent_type": "explore",
            "agent_id": "a1", "session_id": "s1", "dispatch_id": "s1:a1",
            "request_source": "claude-code",
        }) + "\n", encoding="utf-8")
        self.env = {**os.environ,
                    "AGENT_EXPERIENCE_PENDING": str(pending),
                    "AGENT_EXPERIENCE_LEDGER": str(temp / "ledger.jsonl"),
                    "AGENT_CLAUDE_RESOLVER": str(
                        ROOT / "main/claude/scripts/model-routing")}
        subprocess.run(
            [sys.executable, str(self.HOOK)], env=self.env, check=True,
            capture_output=True, text=True,
            input=json.dumps({"hook_event_name": "SubagentStop",
                              "agent_type": "explore", "agent_id": "a1",
                              "session_id": "s1",
                              "transcript_path": str(transcript)}))
        stubs = [json.loads(line) for line in
                 pending.read_text(encoding="utf-8").splitlines()]
        return stubs[-1]

    def _log(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.LOG), "--from-pending",
             "--outcome", "accepted", "--class", "recon", *extra],
            env=self.env, capture_output=True, text=True)

    def _record(self, temp: Path) -> dict:
        return json.loads(
            (temp / "ledger.jsonl").read_text(encoding="utf-8").splitlines()[-1])

    def test_hook_stages_the_model_claude_actually_ran(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stub = self._stage(Path(temp_dir), ["claude-sonnet-5"] * 3)
            self.assertEqual(stub["observed_model"], "claude-sonnet-5")
            # Same pass still reports usage; the model is read alongside it.
            self.assertEqual(stub["tokens_in"], 300)

    def test_transcript_attested_route_may_drive_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            self._stage(temp, ["claude-sonnet-5"])
            result = self._log()
            self.assertEqual(result.returncode, 0, result.stderr)
            record = self._record(temp)
            # Model from the transcript, the rest from the resolved pin.
            self.assertEqual(record["model"], "claude-sonnet-5")
            self.assertEqual(record["route_source"], "transcript-verified")
            self.assertIn(record["route_source"], DECISION_ROUTE_SOURCES)

    def test_a_claimed_model_the_transcript_contradicts_is_rejected(self) -> None:
        # The dispatcher's claim is checked against evidence, exactly as on the
        # bridge; disagreement is a routing violation, not a record.
        with tempfile.TemporaryDirectory() as temp_dir:
            self._stage(Path(temp_dir), ["claude-sonnet-5"])
            result = self._log("--model", "claude-opus-5")
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertIn("contradicts the provider-recorded route",
                          result.stderr)

    def test_a_dated_snapshot_attests_the_generation_it_belongs_to(self) -> None:
        """`claude-sonnet-5-20260601` is the pinned model, not a mismatch.

        The CLI reports dated ids where the routing config declares undated
        ones. Reading that as a contradiction would refuse every dispatch of
        an affected tier; recording the dated id instead would split its
        cohort away from the config's own name for the same model.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            self._stage(temp, ["claude-sonnet-5-20260601"])
            result = self._log()
            self.assertEqual(result.returncode, 0, result.stderr)
            record = self._record(temp)
            self.assertEqual(record["model"], "claude-sonnet-5")
            self.assertEqual(record["route_source"], "transcript-verified")

    def test_a_generation_move_is_refused_rather_than_logged(self) -> None:
        # The alias moved under the pin: the resolver still says sonnet-5, the
        # transcript says otherwise. `check-aliases` reports this weekly; the
        # logger must not quietly file the dispatch under a model that did not
        # run, which is what made the alias assertion worth testing at all.
        with tempfile.TemporaryDirectory() as temp_dir:
            self._stage(Path(temp_dir), ["claude-sonnet-6"])
            result = self._log()
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertIn("contradicts the provider-recorded route",
                          result.stderr)

    def test_an_unattestable_transcript_claims_no_route(self) -> None:
        """Two models in one transcript attest nothing; a local turn is not one.

        Claude Code writes `<synthetic>` for turns it produced itself (API
        errors, interrupts). Counting that as a second model would strip the
        attestation off an ordinary dispatch.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            stub = self._stage(temp, ["claude-sonnet-5", "claude-opus-5"])
            self.assertNotIn("observed_model", stub)
            self.assertEqual(stub["telemetry_warning"],
                             "ambiguous_transcript_model")
            result = self._log()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self._record(temp)["route_source"],
                             "resolver-assumed")
        with tempfile.TemporaryDirectory() as temp_dir:
            stub = self._stage(Path(temp_dir),
                               ["claude-sonnet-5", "<synthetic>", None])
            self.assertEqual(stub["observed_model"], "claude-sonnet-5")


class NativeCodexStagingTests(unittest.TestCase):
    """Native Codex has no dispatch hook, so the dispatcher stages the carrier.

    Without one, a native Codex dispatch had no launched/collected carrier at
    all: an outcome that never reached the ledger left nothing behind for
    `weekly-integrity` to find. The omissions are not random — a hard or failed
    dispatch is the likeliest one to be abandoned — so the missing records bias
    the cohorts that steer later routing.
    """

    STAGE = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-stage"
    LOG = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-log"
    ROUTE = ("--profile", "balanced", "--model", "gpt-5.6", "--effort", "high")

    def _env(self, temp: Path) -> dict:
        return {**os.environ,
                "AGENT_EXPERIENCE_PENDING": str(temp / "pending.jsonl"),
                "AGENT_EXPERIENCE_LEDGER": str(temp / "ledger.jsonl")}

    def _stage(self, env: dict, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(self.STAGE), *args],
                              env=env, capture_output=True, text=True)

    def _rows(self, temp: Path) -> list[dict]:
        path = temp / "pending.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in
                path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_abandon_closes_only_what_nobody_can_still_judge(self) -> None:
        """The escape hatch has to be a bad one.

        On 2026-08-06 twenty-three stubs from a session ten days gone had no
        reachable reviewer, and the pending file had to be hand-edited because
        `--cancel` refuses anything that ran and an outcome is a judgement
        nobody could still make. `--abandon` is that missing close, so what
        matters is that it stays useless for the case it must not serve: a
        fresh dispatch whose owner simply has not done QC yet.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = {**self._env(temp),
                   "AGENT_EXPERIENCE_ABANDONED": str(temp / "abandoned.jsonl")}
            old = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(
                timespec="seconds")
            fresh = datetime.now(timezone.utc).isoformat(timespec="seconds")
            (temp / "pending.jsonl").write_text("\n".join(json.dumps(row) for row in [
                {"ts": old, "event": "SubagentStop", "agent_type": "explore",
                 "dispatch_id": "s:old", "secs": 3},
                {"ts": fresh, "event": "SubagentStop", "agent_type": "explore",
                 "dispatch_id": "s:fresh", "secs": 3},
                {"ts": old, "event": "SubagentStart", "agent_type": "explore",
                 "dispatch_id": "s:neverran"},
            ]) + "\n", encoding="utf-8")

            done = self._stage(env, "--abandon", "--dispatch-id", "s:old",
                               "--reason", "session gone")
            self.assertEqual(done.returncode, 0, done.stderr)
            audit = [json.loads(line) for line in
                     (temp / "abandoned.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(audit[0]["dispatch_id"], "s:old")
            self.assertEqual(audit[0]["reason"], "session gone")
            # The audit row is a sibling of the ledger, never a row in it: an
            # abandoned dispatch has no outcome and must reach no metric.
            self.assertFalse((temp / "ledger.jsonl").exists()
                             and (temp / "ledger.jsonl").read_text().strip())
            self.assertNotIn("s:old", [r.get("dispatch_id") for r in self._rows(temp)])

            fresh_run = self._stage(env, "--abandon", "--dispatch-id", "s:fresh",
                                    "--reason", "cannot be bothered")
            self.assertNotEqual(fresh_run.returncode, 0)
            self.assertIn("not for skipping QC", fresh_run.stderr)

            never = self._stage(env, "--abandon", "--dispatch-id", "s:neverran",
                                "--reason", "x")
            self.assertNotEqual(never.returncode, 0)
            self.assertIn("--cancel", never.stderr)

            unexplained = self._stage(env, "--abandon", "--dispatch-id", "s:old")
            self.assertNotEqual(unexplained.returncode, 0)
            self.assertIn("--reason", unexplained.stderr)

    def test_launch_and_completion_reach_the_ledger_as_one_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            started = self._stage(env, "--start", "--role", "executor",
                                  "--session", "codex-s1")
            self.assertEqual(started.returncode, 0, started.stderr)
            dispatch_id = started.stdout.strip()
            self.assertTrue(dispatch_id.startswith("codex-s1:"), dispatch_id)
            launch = self._rows(temp)[-1]
            self.assertEqual(launch["event"], "SubagentStart")
            self.assertEqual(launch["agent_type"], "executor")
            self.assertEqual(launch["request_source"], "codex")

            stopped = self._stage(env, "--stop", "--dispatch-id", dispatch_id)
            self.assertEqual(stopped.returncode, 0, stopped.stderr)
            completion = self._rows(temp)[-1]
            self.assertEqual(completion["event"], "SubagentStop")
            self.assertGreaterEqual(completion["secs"], 0)

            logged = subprocess.run(
                [sys.executable, str(self.LOG), "--from-pending",
                 "--dispatch-id", dispatch_id, "--outcome", "accepted",
                 "--class", "impl", *self.ROUTE],
                env=env, capture_output=True, text=True)
            self.assertEqual(logged.returncode, 0, logged.stderr)
            record = json.loads(
                (temp / "ledger.jsonl").read_text(encoding="utf-8").splitlines()[-1])
            # Role, provider and request source all come from the staged launch;
            # only the route (which Codex does not attest here) is typed in.
            self.assertEqual(record["role"], "executor")
            self.assertEqual(record["provider"], "codex")
            self.assertEqual(record["request_source"], "codex")
            self.assertEqual(record["dispatch_id"], dispatch_id)
            self.assertEqual(record["route_source"], "explicit")
            # Reconciled: nothing left for the weekly check to report.
            self.assertEqual(self._rows(temp), [])

    def test_a_failed_dispatch_is_logged_like_any_other(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            dispatch_id = self._stage(
                env, "--start", "--role", "verifier").stdout.strip()
            self._stage(env, "--stop", "--dispatch-id", dispatch_id)
            logged = subprocess.run(
                [sys.executable, str(self.LOG), "--from-pending",
                 "--dispatch-id", dispatch_id, "--outcome", "failed",
                 "--class", "verify", *self.ROUTE],
                env=env, capture_output=True, text=True)
            self.assertEqual(logged.returncode, 0, logged.stderr)
            record = json.loads(
                (temp / "ledger.jsonl").read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(record["outcome"], "failed")
            self.assertEqual(self._rows(temp), [])

    def test_reusing_a_dispatch_id_is_refused(self) -> None:
        """Two dispatches under one id would file one outcome for both."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            first = self._stage(env, "--start", "--role", "explore",
                                "--dispatch-id", "codex:reused")
            self.assertEqual(first.returncode, 0, first.stderr)
            again = self._stage(env, "--start", "--role", "explore",
                                "--dispatch-id", "codex:reused")
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("already staged", again.stderr)
            self.assertEqual(len(self._rows(temp)), 1)

    def test_a_cancelled_launch_leaves_nothing_to_reconcile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            dispatch_id = self._stage(
                env, "--start", "--role", "executor").stdout.strip()
            cancelled = self._stage(env, "--cancel", "--dispatch-id", dispatch_id)
            self.assertEqual(cancelled.returncode, 0, cancelled.stderr)
            self.assertEqual(self._rows(temp), [])
            # A cancel that matches nothing is a typo, not a no-op: silently
            # succeeding would let a real launch stay staged and unreported.
            twice = self._stage(env, "--cancel", "--dispatch-id", dispatch_id)
            self.assertNotEqual(twice.returncode, 0)
            self.assertIn("nothing staged", twice.stderr)

    def test_cancelling_a_dispatch_that_ran_is_refused(self) -> None:
        """`--cancel` may only retire a launch whose leaf never ran.

        Deleting a launch *and* its staged completion removes the only carrier
        weekly reconciliation can see, so a dispatch that ran and was never
        logged becomes undetectable again — and the hard and failed ones are
        the likeliest to be abandoned that way, which is the success bias this
        script exists to prevent (2026-07-30 review).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            dispatch_id = self._stage(
                env, "--start", "--role", "executor").stdout.strip()
            self.assertEqual(
                self._stage(env, "--stop", "--dispatch-id", dispatch_id).returncode,
                0)
            cancelled = self._stage(env, "--cancel", "--dispatch-id", dispatch_id)
            self.assertNotEqual(cancelled.returncode, 0, cancelled.stdout)
            self.assertIn("its leaf ran", cancelled.stderr)
            # Refusing is only half of it: both rows have to survive, or the
            # carrier is gone whatever the exit status said.
            self.assertEqual(
                [row["event"] for row in self._rows(temp)],
                ["SubagentStart", "SubagentStop"])
            # The named alternative has to actually work, or the refusal just
            # teaches the dispatcher to stop staging.
            logged = subprocess.run(
                [sys.executable, str(self.LOG), "--from-pending",
                 "--dispatch-id", dispatch_id, "--outcome", "failed",
                 "--class", "impl", *self.ROUTE],
                env=env, capture_output=True, text=True)
            self.assertEqual(logged.returncode, 0, logged.stderr)
            self.assertEqual(self._rows(temp), [])

    def test_a_logged_dispatch_id_cannot_be_staged_again(self) -> None:
        """Uniqueness is against the ledger, not only the pending file.

        Logging clears the stub, so the pending file stops recognising an id
        the moment it is reconciled. `weekly-integrity` skips every id the
        ledger already names, so a reused id is permanently immune to the
        un-reconciled alarm — the same silent-omission class as cancelling a
        dispatch that ran (2026-07-30 review).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            dispatch_id = self._stage(
                env, "--start", "--role", "executor",
                "--dispatch-id", "codex:reused-after-log").stdout.strip()
            self._stage(env, "--stop", "--dispatch-id", dispatch_id)
            logged = subprocess.run(
                [sys.executable, str(self.LOG), "--from-pending",
                 "--dispatch-id", dispatch_id, "--outcome", "accepted",
                 "--class", "impl", *self.ROUTE],
                env=env, capture_output=True, text=True)
            self.assertEqual(logged.returncode, 0, logged.stderr)
            # The stub is gone, which is exactly why the pending file alone
            # cannot answer the question.
            self.assertEqual(self._rows(temp), [])
            again = self._stage(env, "--start", "--role", "executor",
                                "--dispatch-id", dispatch_id)
            self.assertNotEqual(again.returncode, 0, again.stdout)
            self.assertIn("already in the ledger", again.stderr)
            self.assertEqual(self._rows(temp), [])

    def test_a_completion_needs_its_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            orphan = self._stage(env, "--stop", "--dispatch-id", "codex:ghost")
            self.assertNotEqual(orphan.returncode, 0)
            self.assertIn("no staged launch", orphan.stderr)
            dispatch_id = self._stage(
                env, "--start", "--role", "executor").stdout.strip()
            self._stage(env, "--stop", "--dispatch-id", dispatch_id)
            repeated = self._stage(env, "--stop", "--dispatch-id", dispatch_id)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("already has a staged completion", repeated.stderr)

    def test_concurrent_completions_still_require_a_dispatch_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            ids = []
            for role in ("explore", "executor"):
                dispatch_id = self._stage(
                    env, "--start", "--role", role).stdout.strip()
                self._stage(env, "--stop", "--dispatch-id", dispatch_id)
                ids.append(dispatch_id)
            ambiguous = subprocess.run(
                [sys.executable, str(self.LOG), "--from-pending",
                 "--outcome", "accepted", "--class", "impl", *self.ROUTE],
                env=env, capture_output=True, text=True)
            self.assertNotEqual(ambiguous.returncode, 0)
            self.assertIn("multiple completed dispatches", ambiguous.stderr)
            for dispatch_id in ids:
                self.assertIn(dispatch_id, ambiguous.stderr)
            # Naming one pairs the outcome with that dispatch and leaves the
            # other staged, so the second is still reconcilable afterwards.
            picked = subprocess.run(
                [sys.executable, str(self.LOG), "--from-pending",
                 "--dispatch-id", ids[0], "--outcome", "accepted",
                 "--class", "recon", *self.ROUTE],
                env=env, capture_output=True, text=True)
            self.assertEqual(picked.returncode, 0, picked.stderr)
            remaining = {row["dispatch_id"] for row in self._rows(temp)}
            self.assertEqual(remaining, {ids[1]})

    def test_stager_and_logger_agree_on_loggable_roles(self) -> None:
        """A staged role the logger would not accept stages an unloggable stub.

        Extended 2026-08-06 to a third list. `weekly-integrity` decides which
        forgotten stubs get named, and a role missing from it as well as from
        the logger is unloggable and unreported at once: 60 `general-purpose`
        stubs accumulated in silence that way, because nothing could log them
        and nothing complained. The extractor also has to survive a role name
        with punctuation in it — the old `[a-z-]+` pattern quietly dropped
        `codex:codex-rescue`, so the sets could disagree on that name and still
        compare equal.
        """
        stage_source = read(".agents/skills/experience-ledger/scripts/experience-stage")
        log_source = read(".agents/skills/experience-ledger/scripts/experience-log")
        weekly_source = read(".claude/hooks/weekly-integrity.py")

        def names(source: str, marker: str, closer: str = ")") -> set[str]:
            block = source.split(marker, 1)[1]
            return set(re.findall(r'"([^"]+)"', block[:block.index(closer)]))

        routed = names(log_source, "ROUTED_ROLES = (")
        loggable = routed | names(log_source, "DIAGNOSTIC_ROLES = (")
        self.assertEqual(loggable, names(stage_source, "ROLES = ("))
        self.assertEqual(loggable, names(weekly_source, "loggable_roles = {", "}"))
        # The routed half is exactly what model-routing pins. Keeping the
        # diagnostic half out of it is what stops a cohort nothing routes from
        # producing a hint or a revision.
        self.assertEqual(routed, set(ROLES))
        config = tomllib.loads(read("main/claude/model-routing.toml"))
        self.assertEqual(routed, set(config["route_application"]["roles"]) - {"main"})
        self.assertFalse(routed & names(log_source, "DIAGNOSTIC_ROLES = ("))
        self.assertTrue(os.access(self.STAGE, os.X_OK))


class LedgerUniquenessTests(unittest.TestCase):
    """One dispatch, one record - the cardinality every metric is computed on.

    `experience-report` and `experience-revise` count ledger rows, not
    dispatches. A dispatch filed twice is therefore two samples of an event
    that happened once, and if the two rows disagree on `outcome` it is two
    samples that contradict each other. The append used to be unconditional,
    so a retry, a concurrent logger, or a rerun after pending cleanup failed
    all produced exactly that (2026-07-30 review).
    """

    STAGE = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-stage"
    LOG = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-log"
    ROUTE = ("--profile", "balanced", "--model", "gpt-5.6", "--effort", "high")
    IDENT = ("--role", "executor", "--provider", "codex",
             "--request-source", "codex", "--class", "impl", "--task", "probe")

    def _env(self, temp: Path) -> dict:
        return {**os.environ,
                "AGENT_EXPERIENCE_PENDING": str(temp / "pending.jsonl"),
                "AGENT_EXPERIENCE_LEDGER": str(temp / "ledger.jsonl")}

    def _log(self, env: dict, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(self.LOG), *args],
                              env=env, capture_output=True, text=True)

    def _ledger(self, temp: Path) -> list[dict]:
        path = temp / "ledger.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in
                path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_a_second_outcome_for_one_dispatch_is_refused(self) -> None:
        """The contradictory case, because it is the one that misleads.

        Two rows for one dispatch inflate `observed_n`; two rows that disagree
        on the outcome also make the acceptance rate a number no sequence of
        real dispatches could produce.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            first = self._log(env, "--dispatch-id", "codex:once",
                              "--outcome", "accepted", *self.IDENT, *self.ROUTE)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self._log(env, "--dispatch-id", "codex:once",
                               "--outcome", "failed", *self.IDENT, *self.ROUTE)
            self.assertNotEqual(second.returncode, 0, second.stdout)
            self.assertIn("already in the ledger", second.stderr)
            rows = self._ledger(temp)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["outcome"], "accepted")

    def test_a_record_without_a_dispatch_id_is_never_treated_as_a_duplicate(self) -> None:
        """Legacy and hand-written rows carry no id and must stay loggable.

        Deduplicating on a missing key would collapse every such row into one
        and silently drop real samples - the opposite failure of the same
        cardinality bug.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            for _ in range(2):
                run = self._log(env, "--outcome", "accepted",
                                *self.IDENT, *self.ROUTE)
                self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(len(self._ledger(temp)), 2)

    def test_a_refused_duplicate_still_clears_the_stale_stub(self) -> None:
        """The retry path has to end somewhere.

        Pending cleanup is best-effort and prints a WARN while exiting 0, which
        invites a rerun. The rerun is now refused, and `experience-stage
        --cancel` deliberately refuses an id the ledger names - so unless the
        refusal itself reconciles the stub, that stub has no exit at all and
        sits in the pending file as a permanent un-reconciled dispatch.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            pending = temp / "pending.jsonl"
            for stage_args in (("--start", "--role", "executor",
                                "--dispatch-id", "codex:stale"),
                               ("--stop", "--dispatch-id", "codex:stale")):
                staged = subprocess.run(
                    [sys.executable, str(self.STAGE), *stage_args],
                    env=env, capture_output=True, text=True)
                self.assertEqual(staged.returncode, 0, staged.stderr)
            # The exact bytes the staging path writes, kept so the stub can be
            # restored: a hand-built one would not match what cleanup consumes.
            staged_bytes = pending.read_text(encoding="utf-8")
            self.assertEqual(
                self._log(env, "--dispatch-id", "codex:stale", "--outcome",
                          "accepted", *self.IDENT, *self.ROUTE).returncode, 0)
            self.assertEqual(pending.read_text(encoding="utf-8").strip(), "")
            # Now the cleanup-failure state: record filed, stub still there.
            pending.write_text(staged_bytes, encoding="utf-8")
            refused = self._log(env, "--dispatch-id", "codex:stale",
                                "--outcome", "accepted", *self.IDENT, *self.ROUTE)
            self.assertNotEqual(refused.returncode, 0, refused.stdout)
            self.assertEqual(len(self._ledger(temp)), 1, "refusal still appended")
            self.assertEqual(
                pending.read_text(encoding="utf-8").strip(), "",
                "the stub survived a refusal, so nothing can ever retire it")
            # And the alternative the refusal names must not be the cancel path,
            # which is closed by design.
            cancelled = subprocess.run(
                [sys.executable, str(self.STAGE), "--cancel",
                 "--dispatch-id", "codex:stale"],
                env=env, capture_output=True, text=True)
            self.assertNotEqual(cancelled.returncode, 0)

    def test_the_lifecycle_lock_is_actually_held(self) -> None:
        """Two loggers started together prove the check, not the lock.

        Python startup dominates, so they serialise on their own and the pair
        would pass with no lock at all. The lock is only refutable by holding
        it: this takes the pending lock - the one both writers share, since
        `experience-stage` does its ledger read inside it - from outside and
        asserts the logger blocks and writes nothing until it is released.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            pending = temp / "pending.jsonl"
            pending.write_text("", encoding="utf-8")
            command = [sys.executable, str(self.LOG), "--dispatch-id",
                       "codex:locked", "--outcome", "accepted",
                       *self.IDENT, *self.ROUTE]
            with open(str(pending) + ".lock", "a", encoding="utf-8") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                running = subprocess.Popen(command, env=env, text=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                try:
                    running.wait(timeout=3)
                    running.stdout.close()
                    running.stderr.close()
                    self.fail("the logger committed while the lifecycle lock "
                              f"was held (rc={running.returncode})")
                except subprocess.TimeoutExpired:
                    self.assertEqual(self._ledger(temp), [])
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            self.assertEqual(running.wait(timeout=60), 0)
            running.stdout.close()
            running.stderr.close()
            self.assertEqual(len(self._ledger(temp)), 1)

    def test_an_outcome_cannot_be_logged_while_the_leaf_is_still_running(self) -> None:
        """A staged launch with no completion has no outcome to record.

        The logger only ever read the ledger, never the pending file, so
        `--start` followed by an explicit log needed no race at all to seal a
        live dispatch: the outcome was written, and from then on the real one
        could not be logged (id in the ledger), the launch could not be
        cancelled (it had run), and reconciliation skips every id the ledger
        names - so nothing reported it (2026-07-30 re-review).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            self.assertEqual(
                subprocess.run([sys.executable, str(self.STAGE), "--start",
                                "--role", "executor", "--dispatch-id",
                                "codex:live"],
                               env=env, capture_output=True,
                               text=True).returncode, 0)
            premature = self._log(env, "--dispatch-id", "codex:live",
                                  "--outcome", "accepted", *self.IDENT,
                                  *self.ROUTE)
            self.assertNotEqual(premature.returncode, 0, premature.stdout)
            self.assertIn("still in flight", premature.stderr)
            self.assertEqual(self._ledger(temp), [], "an outcome was recorded")
            # The carrier must survive: it is the only thing that will report
            # this dispatch if its outcome is forgotten, and the premature log
            # is the mistake, not the launch.
            rows = [json.loads(line) for line in
                    (temp / "pending.jsonl").read_text(
                        encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual([row["event"] for row in rows], ["SubagentStart"])
            # The route the refusal names has to work, or the refusal just
            # teaches the dispatcher to stop staging launches.
            self.assertEqual(
                subprocess.run([sys.executable, str(self.STAGE), "--stop",
                                "--dispatch-id", "codex:live"],
                               env=env, capture_output=True,
                               text=True).returncode, 0)
            real = self._log(env, "--from-pending", "--dispatch-id",
                             "codex:live", "--outcome", "failed",
                             "--class", "impl", "--task", "probe", *self.ROUTE)
            self.assertEqual(real.returncode, 0, real.stderr)
            self.assertEqual([row["outcome"] for row in self._ledger(temp)],
                             ["failed"])

    def test_a_running_dispatch_and_a_mistyped_id_read_differently(self) -> None:
        """Two states, opposite responses, one message until 2026-07-31.

        `--from-pending` failed with "no staged SubagentStop stub found" both
        when the leaf was still running and when the id did not exist. Hit for
        real during a fifteen-dispatch batch: one log call landed a second
        before that leaf's SubagentStop hook, and the message sent the reader
        looking for a logging defect instead of waiting. The in-flight guard
        already phrased this correctly on the explicit-flag path; the
        `--from-pending` path returned before reaching it.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            self.assertEqual(
                subprocess.run(
                    [sys.executable, str(self.STAGE), "--start", "--role",
                     "executor", "--dispatch-id", "codex:running"],
                    env=env, capture_output=True, text=True).returncode, 0)

            running = self._log(env, "--from-pending", "--dispatch-id",
                                "codex:running", "--outcome", "accepted",
                                "--class", "impl", "--task", "probe",
                                *self.ROUTE)
            typo = self._log(env, "--from-pending", "--dispatch-id",
                             "codex:nosuchid", "--outcome", "accepted",
                             "--class", "impl", "--task", "probe", *self.ROUTE)
            for run in (running, typo):
                self.assertNotEqual(run.returncode, 0, run.stdout)
            self.assertIn("still in flight", running.stderr)
            self.assertNotIn("still in flight", typo.stderr)
            self.assertIn("check the dispatch id", typo.stderr)
            self.assertIn("codex:nosuchid", typo.stderr,
                          "the id that matched nothing has to be named")
            self.assertEqual(self._ledger(temp), [], "a refusal wrote a record")

            # And the state the message tells the reader to wait for must work.
            self.assertEqual(
                subprocess.run(
                    [sys.executable, str(self.STAGE), "--stop",
                     "--dispatch-id", "codex:running"],
                    env=env, capture_output=True, text=True).returncode, 0)
            done = self._log(env, "--from-pending", "--dispatch-id",
                             "codex:running", "--outcome", "accepted",
                             "--class", "impl", "--task", "probe", *self.ROUTE)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(len(self._ledger(temp)), 1)

    def test_a_corrupt_byte_in_the_ledger_cannot_stop_logging(self) -> None:
        """Decoding runs before json.loads, so a bad byte is not a bad row.

        Reading the ledger before appending began on 2026-07-30. Until this,
        one half-written multi-byte character anywhere in the file raised
        UnicodeDecodeError in every subsequent run of both scripts — the ledger
        became append-dead until repaired by hand, which is a worse failure
        than the duplicate the read was added to prevent.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            (temp / "ledger.jsonl").write_bytes(
                json.dumps({"dispatch_id": "codex:known",
                            "outcome": "accepted"}).encode("utf-8")
                + b"\n\xff\xfe truncated\n")
            fresh = self._log(env, "--dispatch-id", "codex:new", "--outcome",
                              "accepted", *self.IDENT, *self.ROUTE)
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            staged = subprocess.run(
                [sys.executable, str(self.STAGE), "--start", "--role",
                 "executor", "--dispatch-id", "codex:other"],
                env=env, capture_output=True, text=True)
            self.assertEqual(staged.returncode, 0, staged.stderr)
            # Replacing undecodable bytes must not blind the guard to the ids
            # on the rows that are intact.
            duplicate = self._log(env, "--dispatch-id", "codex:known",
                                  "--outcome", "accepted", *self.IDENT,
                                  *self.ROUTE)
            self.assertNotEqual(duplicate.returncode, 0, duplicate.stdout)
            self.assertIn("already in the ledger", duplicate.stderr)

    def test_both_scripts_read_the_same_ids_out_of_one_ledger(self) -> None:
        """`experience-log` and `experience-stage` scan the ledger separately.

        They share no import path, so the scan is written twice; a divergence
        would leave one door open while the other is shut. Asserted on
        behaviour against one ledger rather than on the text of either copy.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            (temp / "ledger.jsonl").write_text(
                "\n".join([
                    json.dumps({"dispatch_id": "codex:known", "outcome": "accepted"}),
                    "",                       # blank line
                    "{ not json",             # malformed row: skipped, not fatal
                    json.dumps({"outcome": "accepted"}),   # no id at all
                ]) + "\n", encoding="utf-8")
            staged = subprocess.run(
                [sys.executable, str(self.STAGE), "--start", "--role",
                 "executor", "--dispatch-id", "codex:known"],
                env=env, capture_output=True, text=True)
            logged = self._log(env, "--dispatch-id", "codex:known",
                               "--outcome", "accepted", *self.IDENT, *self.ROUTE)
            for name, run in (("stage", staged), ("log", logged)):
                self.assertNotEqual(run.returncode, 0, f"{name}: {run.stdout}")
                self.assertIn("already in the ledger", run.stderr, name)
            # A corrupt neighbouring row must not have been what refused them.
            fresh = self._log(env, "--dispatch-id", "codex:unknown",
                              "--outcome", "accepted", *self.IDENT, *self.ROUTE)
            self.assertEqual(fresh.returncode, 0, fresh.stderr)

    # The pending file has four readers and had four different answers to one
    # damaged row: the logger read the whole file as empty, `experience-stage`
    # raised, `weekly-integrity` aborted its entire run, and the hook wrote no
    # stub at all. Only the ledger side was hardened on 2026-07-30, and the
    # pending file is the one a hook appends to on every subagent stop.
    DAMAGED = JSONL_DAMAGE

    def _pending_with_damage(self, temp: Path, damage: bytes, event: str) -> None:
        row = {
            "ts": "2026-07-31T00:00:00+00:00", "event": event,
            "agent_type": "explore", "agent_id": "a1", "session_id": "s1",
            "dispatch_id": "s1:a1", "request_source": "claude-code",
        }
        (temp / "pending.jsonl").write_bytes(
            json.dumps(row).encode("utf-8") + b"\n" + damage)

    def test_a_damaged_pending_row_cannot_blind_the_in_flight_guard(self) -> None:
        """The dangerous direction: unreadable must not be read as "not in flight".

        `read_pending_rows` returned `[]` for the whole file on one malformed
        line, and `in_flight` reads no rows as no launch — so a single bad row
        waved through the exact write the guard was added to refuse: an outcome
        for a leaf still running, which then seals the id against the real one.
        """
        for name, damage in self.DAMAGED:
            with self.subTest(name), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                env = self._env(temp)
                self._pending_with_damage(temp, damage, "SubagentStart")
                run = self._log(env, "--dispatch-id", "s1:a1", "--outcome",
                                "accepted", *self.IDENT, *self.ROUTE)
                self.assertNotEqual(run.returncode, 0, run.stdout)
                self.assertIn("still in flight", run.stderr)
                self.assertEqual(self._ledger(temp), [], "outcome was recorded")

    def test_a_damaged_pending_row_cannot_stop_staging(self) -> None:
        """`experience-stage` died on an uncaught traceback instead.

        A native Codex dispatch that cannot stage a launch has no carrier at
        all, which is the invisible-dispatch success bias the script exists to
        prevent — reintroduced by one bad byte in a file it only reads.
        """
        for name, damage in self.DAMAGED:
            with self.subTest(name), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                env = self._env(temp)
                self._pending_with_damage(temp, damage, "SubagentStart")
                staged = subprocess.run(
                    [sys.executable, str(self.STAGE), "--start", "--role",
                     "executor", "--dispatch-id", "codex:new"],
                    env=env, capture_output=True, text=True)
                self.assertEqual(staged.returncode, 0, staged.stderr)
                self.assertIn("codex:new", (temp / "pending.jsonl")
                              .read_text(encoding="utf-8", errors="replace"))

    def test_dropping_an_unreadable_pending_row_is_announced(self) -> None:
        """The rewrite is the only automatic repair, so it must not be silent.

        Skipping a damaged row on read means the next rewrite drops it. That is
        the right outcome — it carries no readable dispatch id and can never be
        reconciled — but a cleanup that discards bytes without a word is how a
        repair becomes an unnoticed loss.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            env = self._env(temp)
            for stage_args in (("--start", "--role", "executor",
                                "--dispatch-id", "codex:pair"),
                               ("--stop", "--dispatch-id", "codex:pair")):
                self.assertEqual(subprocess.run(
                    [sys.executable, str(self.STAGE), *stage_args],
                    env=env, capture_output=True, text=True).returncode, 0)
            pending = temp / "pending.jsonl"
            pending.write_bytes(pending.read_bytes() + b"\xff\xfe truncated\n")
            run = self._log(env, "--from-pending", "--dispatch-id", "codex:pair",
                            "--outcome", "accepted", "--class", "impl",
                            "--task", "probe", *self.ROUTE)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("unreadable pending row", run.stderr)
            self.assertEqual(pending.read_text(encoding="utf-8").strip(), "")

    def test_the_ordering_guard_covers_exactly_the_staged_dispatches(self) -> None:
        """Three carrier states, three different correct answers.

        `SKILL.md` claimed the ordering rule was enforced outright. It is not,
        and cannot be: the guard reads the pending file, so an id that was never
        staged has nothing to contradict, and requiring a carrier would refuse
        every legacy and hand-written record. The contract now says so; this
        pins the boundary it names, in both directions - a never-staged id must
        still log, and a staged-but-open one must still be refused.
        """
        cases = (
            ("never staged", (), 0, ""),
            ("launch open", (("--start", "--role", "executor"),), 2,
             "still in flight"),
            ("launch closed", (("--start", "--role", "executor"), ("--stop",)),
             0, ""),
        )
        for name, stages, expected_rc, expected_error in cases:
            with self.subTest(name), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                env = self._env(temp)
                for stage_args in stages:
                    self.assertEqual(subprocess.run(
                        [sys.executable, str(self.STAGE), *stage_args,
                         "--dispatch-id", "codex:case"],
                        env=env, capture_output=True, text=True).returncode, 0)
                run = self._log(env, "--dispatch-id", "codex:case", "--outcome",
                                "accepted", *self.IDENT, *self.ROUTE)
                self.assertEqual(run.returncode, expected_rc,
                                 run.stderr or run.stdout)
                if expected_error:
                    self.assertIn(expected_error, run.stderr)
                    self.assertEqual(self._ledger(temp), [])
                else:
                    self.assertEqual(len(self._ledger(temp)), 1)

    def test_the_hook_still_stages_a_stop_past_a_damaged_row(self) -> None:
        """The silent one, and therefore the worst of the four.

        The hook is fail-open by design, so the UnicodeDecodeError raised while
        it looked up the matching launch never surfaced: it fell through to the
        outer `except Exception`, exited 0, and wrote no completion stub at all.
        Every dispatch after that point lost its carrier with no message
        anywhere — and `weekly-integrity`, which would name the loss, aborted on
        the same byte.
        """
        hook = ROOT / "main/claude/hooks/experience-pending.py"
        start = {
            "ts": "2026-07-31T00:00:00+00:00", "event": "SubagentStart",
            "agent_type": "explore", "agent_id": "a1", "session_id": "s1",
            "dispatch_id": "s1:a1", "request_source": "claude-code",
        }
        for name, damage in self.DAMAGED:
            with self.subTest(name), tempfile.TemporaryDirectory() as temp_dir:
                pending = Path(temp_dir) / "pending.jsonl"
                pending.write_bytes(
                    json.dumps(start).encode("utf-8") + b"\n" + damage)
                run = subprocess.run(
                    [sys.executable, str(hook)],
                    input=json.dumps({"hook_event_name": "SubagentStop",
                                      "agent_type": "explore", "agent_id": "a1",
                                      "session_id": "s1"}),
                    env={**os.environ, "AGENT_EXPERIENCE_PENDING": str(pending)},
                    capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                body = pending.read_text(encoding="utf-8", errors="replace")
                self.assertIn("SubagentStop", body,
                              "the completion carrier was dropped in silence")


class LedgerReaderDamageTests(unittest.TestCase):
    """The two readers the shared damage matrix never reached.

    The matrix was written for the four scripts that *write* telemetry, so
    `experience-report` and `experience-revise` - the two that only read it -
    were never driven through it. Six of the seven classes aborted both with an
    uncaught traceback: the decode sits outside the inner handler in one and
    covers the whole file in the other, and a valid-JSON-but-not-an-object row
    raises TypeError, which the handler does not name (2026-08-02 review).

    Why that mattered more than a crash: `weekly-integrity` runs
    `experience-report` and reads a non-zero exit as an empty report with no
    message, so the weekly path went quiet at the same moment the report died.
    One damaged byte therefore stopped both the dispatch-experience hints and
    the routing revision they feed, permanently and without a word, until
    someone opened the file by hand.
    """

    REPORT = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-report"
    REVISE = ROOT / "main/.agents/skills/experience-ledger/scripts/experience-revise"
    @property
    def RECORD(self) -> dict:
        """A valid record dated relative to now, never to a literal date.

        A pinned `ts` ages out of `revision_policy.days` and the row silently
        stops counting: with the 90-day window and a 2026-07-31 fixture, the
        `records == 2` assertion below would have started failing on
        2026-10-29 - and the commit gate runs this suite, so from that date
        every commit in this repo would have been blocked by a test that had
        nothing to do with the change (2026-08-03 review).
        """
        return {
            "ts": (datetime.now(timezone.utc)
                   - timedelta(days=1)).isoformat(timespec="seconds"),
            "schema": 3, "role": "executor",
            "task_class": "impl", "provider": "claude", "outcome": "accepted",
            "profile": "balanced", "model": "claude-opus-5", "effort": "high",
            "request_source": "claude-code",
        }

    def _ledger(self, temp: Path, damage: bytes) -> dict:
        """A damaged row between two valid ones, so loss is measurable."""
        row = json.dumps(self.RECORD).encode("utf-8") + b"\n"
        path = temp / "ledger.jsonl"
        path.write_bytes(row + damage + row)
        return {**os.environ, "AGENT_EXPERIENCE_LEDGER": str(path)}

    def test_a_wrongly_typed_field_costs_only_its_own_row(self) -> None:
        """The row shape being right does not make its fields right.

        `isinstance(record, dict)` was the whole 2026-08-02 guard, and it only
        answers "is this an object". A field inside it can still be a list or a
        dict, which is valid JSON and raises where nothing catches it. Five of
        these aborted both readers after the previous fix, including `ts_naive`
        - a record with no zone, which is not damage at all.
        """
        for name, override in JSONL_FIELD_DAMAGE:
            with self.subTest(name), tempfile.TemporaryDirectory() as temp_dir:
                bad = json.dumps({**self.RECORD, **override}).encode("utf-8")
                env = self._ledger(Path(temp_dir), bad + b"\n")
                report = subprocess.run(
                    [sys.executable, str(self.REPORT), "--json"],
                    env=env, capture_output=True, text=True)
                self.assertEqual(report.returncode, 0,
                                 f"{name}: {report.stderr}")
                self.assertEqual(json.loads(report.stdout)["records"], 2, name)
                revise = subprocess.run(
                    [sys.executable, str(self.REVISE)],
                    env=env, capture_output=True, text=True)
                self.assertEqual(revise.returncode, 0,
                                 f"{name}: {revise.stderr}")
                self.assertNotIn("Traceback", revise.stderr, name)

    def test_the_two_readers_agree_on_which_fields_are_keyed(self) -> None:
        """Divergence here means one surface counts a row the other drops.

        `experience-report` publishes the evidence and `experience-revise`
        proposes route changes from it, so a record has to survive both or
        neither - the same reason their eligibility rules are kept identical.
        """
        lists = []
        for path in (self.REPORT, self.REVISE):
            body = path.read_text(encoding="utf-8")
            match = re.search(r"KEYED_FIELDS = \((.*?)\)", body, re.DOTALL)
            self.assertIsNotNone(match, f"{path.name} has no KEYED_FIELDS")
            lists.append(tuple(re.findall(r'"([^"]+)"', match.group(1))))
        self.assertEqual(lists[0], lists[1],
                         "the readers disagree on their keyed fields")
        self.assertIn("task_class", lists[0], "the guard covers nothing useful")

    def test_a_damaged_ledger_row_costs_only_itself(self) -> None:
        for name, damage in JSONL_DAMAGE:
            with self.subTest(name), tempfile.TemporaryDirectory() as temp_dir:
                env = self._ledger(Path(temp_dir), damage)
                report = subprocess.run(
                    [sys.executable, str(self.REPORT), "--json"],
                    env=env, capture_output=True, text=True)
                self.assertEqual(report.returncode, 0, report.stderr)
                # Not just "it exited 0": the neighbouring valid rows have to
                # survive, or tolerating damage would just mean losing more.
                self.assertEqual(json.loads(report.stdout)["records"], 2, name)

                revise = subprocess.run(
                    [sys.executable, str(self.REVISE)],
                    env=env, capture_output=True, text=True)
                self.assertEqual(revise.returncode, 0, revise.stderr)
                self.assertNotIn("Traceback", revise.stderr, name)
                self.assertIn("comparable cohorts", revise.stdout, name)

    def test_an_unusable_row_is_counted_rather_than_vanished(self) -> None:
        """Surviving the damage is half of it; saying so is the other half.

        metrics.md promises a rejected record "remains visible in
        `observed_n`", and a row that never became a record cannot keep that
        promise - it has no cohort to be visible in. So it is counted instead.
        Without the count, a hand-written record with no zone and a ledger
        eaten by a torn write read exactly alike: a quiet, slightly smaller
        report (2026-08-04 review).
        """
        for name, damage in JSONL_DAMAGE + tuple(
            (field_name, json.dumps({**self.RECORD, **override}).encode("utf-8")
             + b"\n")
            for field_name, override in JSONL_FIELD_DAMAGE
        ):
            with self.subTest(name), tempfile.TemporaryDirectory() as temp_dir:
                env = self._ledger(Path(temp_dir), damage)
                for reader in (self.REPORT, self.REVISE):
                    result = subprocess.run(
                        [sys.executable, str(reader), "--json"],
                        env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0,
                                     f"{name}/{reader.name}: {result.stderr}")
                    self.assertEqual(
                        json.loads(result.stdout).get("unusable_rows"), 1,
                        f"{name}: {reader.name} did not count the damaged row")

    def test_neither_reader_counts_a_blank_line_as_damage(self) -> None:
        """Absence is not damage, and an alarm that cries wolf gets ignored.

        A trailing or stray newline is what an interrupted append leaves, and
        both readers have to agree it costs nothing - otherwise the count that
        is supposed to mean "this ledger is damaged" fires on an empty line.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            env = self._ledger(Path(temp_dir), b"\n   \n")
            for reader in (self.REPORT, self.REVISE):
                result = subprocess.run(
                    [sys.executable, str(reader), "--json"],
                    env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["unusable_rows"], 0,
                                 f"{reader.name} called a blank line damage")

    def test_both_readers_guard_the_two_classes_that_escape_the_handler(self) -> None:
        """Named in source, because the handler tuple does not name them.

        `except (json.JSONDecodeError, KeyError, ValueError)` reads as if it
        covers a bad line. It does not cover a decode raised by the iteration
        above it, nor a TypeError from subscripting a non-object, and both are
        one edit away from coming back.
        """
        for path in (self.REPORT, self.REVISE):
            body = path.read_text(encoding="utf-8")
            # Membership tested as a bool so a failure names the guard rather
            # than dumping the whole script into the report.
            for guard in ('errors="replace"', "isinstance(record, dict)"):
                self.assertTrue(guard in body,
                                f"{path.name} lost its {guard} guard")


class RequestSourceSchemaTests(unittest.TestCase):
    def test_codex_launched_claude_cli_is_representable(self) -> None:
        for script in ("experience-log", "experience-report", "experience-revise"):
            body = (
                ROOT
                / "main/.agents/skills/experience-ledger/scripts"
                / script
            ).read_text(encoding="utf-8")
            self.assertIn("codex-claude-cli", body, script)
        self.assertIn(
            "codex-claude-cli",
            read(".agents/skills/experience-ledger/references/metrics.md"),
        )


if __name__ == '__main__':
    unittest.main()
