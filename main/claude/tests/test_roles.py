"""Leaf role contracts: roster invariants, twin parity, artifact gates."""
from support import *  # noqa: F401,F403


class AgentRosterTests(unittest.TestCase):
    def test_roster_matches_expected_roles(self) -> None:
        self.assertEqual(
            {p.stem for p in (ROOT / "main/claude/agents").glob("*.md")},
            set(ROLES),
        )

    def test_every_role_owns_its_model_and_is_self_contained(self) -> None:
        for role in ROLES:
            meta = frontmatter(f".claude/agents/{role}.md")
            body = read(f".claude/agents/{role}.md")
            self.assertIn(f"name: {role}\n", meta)
            self.assertRegex(meta, r"(?m)^model:\s*\S+\s*$")
            # Words, not lines: a line budget is raised by writing longer
            # lines, and these role bodies already pack several independent
            # rules into one. The unit has to be the one that cannot be gamed,
            # which is the same CJK-aware count the contract budgets use.
            # Measured on the body alone, so it is comparable with the Codex
            # twin's `developer_instructions`.
            instructions = body.split("---\n", 2)[-1]
            self.assertLessEqual(word_count(instructions), ROLE_BODY_BUDGET, role)
            # Leaf roles never read orchestration docs or name the main contract.
            for forbidden in ("CLAUDE.md", "baton-dispatch", "provider-routing", "orchestration"):
                self.assertNotIn(forbidden, body, f"{role} leaks {forbidden}")

    def test_role_bodies_stay_dense(self) -> None:
        """The word budget bounds a role body's size, not its content.

        Same three figures as the resident contracts, same reason: a body can
        sit under 400 words while padding its rules, while splitting one rule
        into several bullets to look leaner per rule, or while compressed past
        the point where the sentences still say who acts. Caps and floor come
        from measuring all fourteen bodies on 2026-08-04, so this locks in the
        shipped state rather than trimming it.

        Both providers in one loop. A role that drifted on one side only is the
        exact failure twin-parity exists to catch, and reading the two bodies
        apart would let one drift while the other holds.
        """
        floor, cap = ROLE_FILLER_RANGE
        bodies = {
            f"claude/{role}": read(f".claude/agents/{role}.md").split("---\n", 2)[-1]
            for role in ROLES
        }
        bodies.update({
            f"codex/{role}": tomllib.loads(
                read(f".codex/agents/{role}.toml"))["developer_instructions"]
            for role in CODEX_ROLES
        })
        for label, body in bodies.items():
            rules = len(rule_units(body))
            self.assertLessEqual(rules, ROLE_RULE_BUDGET, f"{label}: {rules} rules")
            density = bytes_per_rule(body)
            self.assertLessEqual(
                density, ROLE_BYTES_PER_RULE,
                f"{label}: {density:.1f} bytes per rule")
            filler = filler_ratio(body)
            self.assertLessEqual(
                filler, cap, f"{label}: {filler:.3f} filler")
            self.assertGreaterEqual(
                filler, floor,
                f"{label}: {filler:.3f} filler is below the floor - check that "
                "the compression left the sentences their subjects")

    def test_model_tiers_are_pinned(self) -> None:
        self.assertIn("model: sonnet", frontmatter(".claude/agents/explore.md"))
        self.assertIn("model: sonnet", frontmatter(".claude/agents/mech-executor.md"))
        # User-directed 2026-07-23: sonnet/high left the effort-curve Pareto
        # frontier, so executor joined the Opus tier.
        for role in ("executor", "plan-verifier", "verifier",
                     "security-reviewer", "security-executor"):
            self.assertIn("model: opus", frontmatter(f".claude/agents/{role}.md"), role)

    PINNED_EFFORTS = {"explore": "low", "mech-executor": "medium",
                      "executor": "medium", "plan-verifier": "medium",
                      "verifier": "high", "security-reviewer": "high",
                      "security-executor": "high"}

    def test_every_role_pins_profile_effort(self) -> None:
        for role, effort in self.PINNED_EFFORTS.items():
            self.assertIn(f"effort: {effort}", frontmatter(f".claude/agents/{role}.md"), role)

    def test_capability_split_by_role_kind(self) -> None:
        for role in READ_ONLY_ROLES:
            meta = frontmatter(f".claude/agents/{role}.md")
            self.assertRegex(meta, r"(?m)^tools:\s*.+$")
            self.assertNotIn("Agent", meta)
            self.assertNotIn("Workflow", meta)
            self.assertNotIn("Bash", meta)
            self.assertIn("read-only leaf", read(f".claude/agents/{role}.md"))
        # verifier is a read-only role with one guarded tool (Bash): it uses an
        # allowlist, not a denylist, so no unlisted tool - including any MCP
        # mutation tool (readOnlyHint=false), which readonly-bash never sees -
        # is reachable. A denylist would leave that whole class open.
        for role in WRITER_ROLES:
            meta = frontmatter(f".claude/agents/{role}.md")
            self.assertRegex(meta, r"(?m)^disallowedTools:.*\bAgent\b.*\bWorkflow\b")

    def test_explore_separates_recon_from_adversarial_review(self) -> None:
        for path in (".claude/agents/explore.md", ".codex/agents/explore.toml"):
            body = read(path)
            self.assertIn("task_class: recon", body, path)
            self.assertIn("task_class: review", body, path)
            self.assertIn("named review lens", body, path)
            self.assertIn("semantic seams", body, path)
            self.assertIn("residual blind spots", body, path)

    def test_bash_leaf_roles_never_detach(self) -> None:
        for role in BASH_ROLES:
            body = read(f".claude/agents/{role}.md")
            self.assertIn("commands in the foreground", body)
            self.assertIn("at most 10 minutes", body)
            self.assertIn("absolute working directory", body)
            self.assertIn("required environment", body)
            self.assertIn("inputs", body)

    def test_plan_and_outcome_verifiers_are_vocabulary_separated(self) -> None:
        plan = read(".claude/agents/plan-verifier.md")
        outcome = read(".claude/agents/verifier.md")
        self.assertIn("tools: Read, Glob, Grep", plan)
        self.assertIn("READY", plan)
        self.assertIn("REVISE", plan)
        self.assertNotIn("CONFIRMED", plan)
        self.assertIn("CONFIRMED", outcome)
        self.assertIn("REFUTED", outcome)
        self.assertIn("INCONCLUSIVE", outcome)
        self.assertNotIn("READY", outcome)
        self.assertIn('sandbox_mode = "read-only"', outcome)
        self.assertIn("intermediate evidence", outcome)
        self.assertNotIn("Bash", frontmatter(".claude/agents/verifier.md"))

    def test_refuting_takes_more_than_a_reproducible_defect(self) -> None:
        """Reproducibility alone is the wrong bar, and the cheap fix is a clause.

        A verifier that refutes on any reproducible defect can sink a sound
        change over a cosmetic one. Upstream answers this with a P0-P4 severity
        ladder; that would push new vocabulary into six role files on both
        providers, and the resident cost of a contract is its rule count, so we
        buy a finer restatement of the same failure with real attention.

        The clause below is the whole mechanism. It keeps the finding - the
        advisory half is what stops this from being a licence to stay quiet -
        and moves only the verdict. Locked on both providers because a threshold
        that holds on one side is a threshold the caller cannot rely on
        (2026-08-04).
        """
        for path in (".claude/agents/verifier.md", ".codex/agents/verifier.toml"):
            body = " ".join(read(path).split())
            self.assertIn("changes the acceptance conclusion", body, path)
            self.assertIn("would not change it under `Advisory:`", body, path)
            self.assertIn("never move the verdict for it", body, path)
            # No severity ladder crept in alongside the clause.
            self.assertNotRegex(body, r"\bP[0-4]\b", path)

    def test_security_review_and_execute_are_capability_separated(self) -> None:
        for suffix in ("",):
            reviewer = f".claude/agents/security-reviewer{suffix}.md"
            executor = f".claude/agents/security-executor{suffix}.md"
            for path in (reviewer, executor):
                self.assertIn("model: opus", frontmatter(path))
            self.assertIn("tools: Read, Glob, Grep, WebSearch, WebFetch", read(reviewer))
            self.assertNotIn("Bash", frontmatter(reviewer))
            self.assertIn(
                "approved scope, constraints, abuse case, and done-criteria",
                read(executor),
            )
            self.assertIn(
                f"pre-approval analysis belongs to `security-reviewer{suffix}`",
                read(executor),
            )


class LeafArtifactGateTests(unittest.TestCase):
    """Fable-method decision-point gates mirrored across both providers.

    Structural presence only; behavioral trap fixtures are tracked separately."""

    JUDGMENT_WRITERS = (
        ".claude/agents/executor.md",
        ".claude/agents/security-executor.md",
        ".codex/agents/executor.toml",
        ".codex/agents/security-executor.toml",
    )
    ALL_WRITERS = JUDGMENT_WRITERS + (
        ".claude/agents/mech-executor.md",
        ".codex/agents/mech-executor.toml",
    )

    def test_intent_gate_in_judgment_writers(self) -> None:
        for path in self.JUDGMENT_WRITERS:
            body = read(path)
            self.assertIn("INTENT: code does <X>", body, path)
            self.assertIn("stop and report the conflict instead of editing", body, path)
            self.assertIn("the stop report owes the same filled `INTENT:` line", body, path)

    def test_gate_lines_are_declared_machine_checked_in_every_writer(self) -> None:
        for path in self.ALL_WRITERS:
            self.assertIn("verbatim in English in the exact template shown", read(path), path)
        # The clause names only the lines the role owes, and mech owes no
        # INTENT/TWINS. This once carried a stronger claim — that naming them is
        # what made two bridge seeds improvise drifted lines on 2026-07-23. A
        # commit-by-commit check on 2026-08-04 refuted it: neither mech contract
        # has ever contained either word. The invariant is worth holding on its
        # own terms; the causal story was not evidence.
        for path in (".claude/agents/mech-executor.md", ".codex/agents/mech-executor.toml"):
            body = read(path)
            self.assertNotIn("INTENT", body, path)
            self.assertNotIn("TWINS", body, path)

    def test_owed_line_audit_is_mechanized_in_both_qc_paths(self) -> None:
        # One shared implementation in .agents/scripts; both trees symlink it
        # (same relative depth in the repo and in HOME, synced with --links).
        shared = ROOT / "main/.agents/scripts/qc-gate-lines"
        self.assertTrue(shared.is_file(), shared)
        self.assertTrue(os.access(shared, os.X_OK), f"{shared} must be executable")
        for tree in ("claude", "codex"):
            link = ROOT / "main" / tree / "scripts/qc-gate-lines"
            self.assertTrue(link.is_symlink(), f"{link} must be a symlink")
            self.assertEqual(
                os.readlink(link), "../../.agents/scripts/qc-gate-lines", link
            )
        qc_paths = (
            ".claude/skills/baton-dispatch/SKILL.md",
            ".codex/skills/leaf-dispatch/SKILL.md",
        )
        for path, home in zip(qc_paths, ("~/.claude", "~/.codex")):
            body = " ".join(read(path).split())
            self.assertIn(f"{home}/scripts/qc-gate-lines", body, path)
            # Flags come from QC's own evidence, never the report's claims.
            self.assertIn("never from the report's claims", body, path)

    def test_authority_order_is_scoped_to_intended_behavior(self) -> None:
        for path in (".claude/agents/executor.md", ".codex/agents/executor.toml"):
            body = read(path)
            self.assertIn(
                "explicit user statement > spec > tests > current code behavior", body, path
            )
            self.assertIn("not a statement of intended behavior", body, path)

    def test_twins_gate_is_report_only(self) -> None:
        for path in self.JUDGMENT_WRITERS:
            body = read(path)
            self.assertIn("TWINS: searched <pattern>", body, path)
            self.assertIn("Report only", body, path)

    def test_auth_gate_in_every_writer(self) -> None:
        for path in self.ALL_WRITERS:
            body = read(path)
            self.assertIn('AUTH: user said "<words>"', body, path)
            self.assertIn("never authorization", body, path)

    def test_mech_executor_never_weakens_checks(self) -> None:
        for path in (".claude/agents/mech-executor.md", ".codex/agents/mech-executor.toml"):
            self.assertIn("a stop, not a fix", read(path), path)

    def test_twin_roles_share_semantic_clauses(self) -> None:
        # Twin role contracts are hand-maintained on both platforms; this is
        # the shared semantic core that must not drift apart. Platform wording
        # may differ, but every clause must exist on both sides (case-folded).
        shared = {
            "explore": ["read-only leaf agent", "never delegate",
                        "file:line evidence", "genuinely new or redirected work"],
            "mech-executor": ["never delegate", "weaken", "stop and report",
                              "auth: user said"],
            "executor": ["never delegate", "intent: code does",
                         "stop and report"],
            "plan-verifier": ["ready", "revise", "replacement plan",
                              "untrusted observation"],
            "verifier": ["confirmed", "refuted", "inconclusive",
                         "reproducible counterexample", "never fix",
                         # Injection defence borrowed from Deep Agents'
                         # RubricMiddleware grader: the report is observation,
                         # not instruction, and unconfirmed claims stay unmet.
                         "untrusted observation",
                         # Independence guardrails must not drift apart again
                         # (review F-06): isolation, state parity, no writes.
                         "external state", "git status --short",
                         "must be identical", "snapshot updates"],
            "security-reviewer": ["abuse", "trust boundar"],
            "security-executor": ["weaken", "abuse", "intent: code does",
                                  "auth: user said"],
        }
        self.assertEqual(sorted(shared), sorted(ROLES))
        for role, clauses in shared.items():
            claude = read(f".claude/agents/{role}.md").lower()
            codex = read(f".codex/agents/{role}.toml").lower()
            for clause in clauses:
                self.assertIn(clause, claude, f"{role} (claude): {clause}")
                self.assertIn(clause, codex, f"{role} (codex): {clause}")

    def test_subagent_return_contract_is_two_sided(self) -> None:
        # Deep Agents states the return contract on both the caller side
        # (task-tool description) and the executor side (subagent prompt) so
        # the two cannot drift. Mirror that: the brief guidance and every
        # writer role both say the leaf's final report is the sole channel.
        #
        # The clause names no orchestrator. "all main sees" was Claude's word
        # for the caller and had been copied verbatim into the Codex bundle,
        # where nothing is called main; a leaf reading it either maps it to its
        # own caller or treats the sentence as about somebody else. What the
        # rule actually rests on is that no intermediate work survives the
        # dispatch, which is true on both providers and is what the wording
        # should say.
        anchor = "final report is the authoritative record"
        paths = [".claude/skills/baton-dispatch/references/briefs-and-stops.md",
                 ".codex/skills/leaf-dispatch/SKILL.md"]
        paths += [f".claude/agents/{role}.md" for role in WRITER_ROLES]
        paths += [f".codex/agents/{role}.toml" for role in WRITER_ROLES]
        for path in paths:
            # Normalized: leaf-dispatch is hard-wrapped and the clause may span
            # a line break.
            body = " ".join(read(path).split()).lower()
            self.assertIn(anchor, body, path)
            self.assertNotIn("all main sees", body, path)

    def test_codex_writer_tomls_still_parse(self) -> None:
        for role in ("executor", "mech-executor", "security-executor"):
            agent = tomllib.loads(read(f".codex/agents/{role}.toml"))
            self.assertIn("INTENT" if role != "mech-executor" else "AUTH",
                          agent["developer_instructions"], role)

    def test_qc_fraud_checklist_in_both_main_qc_paths(self) -> None:
        for path in (".claude/skills/baton-dispatch/SKILL.md",
                     ".codex/skills/leaf-dispatch/SKILL.md"):
            body = " ".join(read(path).split())
            self.assertIn("false-completion frauds", body, path)
            self.assertIn("leftover leaf-created scratch files", body, path)
            self.assertIn("pre-existing dirty-worktree files are not debris", body, path)
            # s9 evidence: 4/10 leaves under-reported real twins — a found-0
            # claim is verified by QC's own grep, never accepted on the word.
            self.assertIn("`found 0/none` TWINS claim", body, path)
            self.assertIn("grep the fixed construct across the scope", body, path)

    def test_qc_gate_lines_flags_twins_none_claims_for_grep(self) -> None:
        script = ROOT / "main/.agents/scripts/qc-gate-lines"

        def run(report: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(script), "-", "--defect-fixed"],
                input=report, capture_output=True, text=True, timeout=30,
            )

        none_claim = run("TWINS: searched round( - found 0 other sites: none")
        self.assertEqual(none_claim.returncode, 0)
        self.assertIn("VERIFY TWINS", none_claim.stdout)
        counted = run("TWINS: searched round( - found 2 other sites: a.py, b.py")
        self.assertEqual(counted.returncode, 0)
        self.assertNotIn("VERIFY TWINS", counted.stdout)
        self.assertIn("OK", counted.stdout)

    def test_qc_gate_lines_derives_intent_owed_from_the_diff(self) -> None:
        # s9: 4/10 leaves omitted INTENT entirely; the flag must come from the
        # diff mechanically, not from the reviewer remembering to set it.
        script = ROOT / "main/.agents/scripts/qc-gate-lines"
        code_diff = ("--- a/pricebook.py\n+++ b/pricebook.py\n@@ -1 +1 @@\n"
                     "-old\n+new\n")
        docs_diff = ("--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n"
                     "-old\n+new\n")
        # Whole-file deletions/additions pair a real path with /dev/null; the
        # header pair must be judged together or deletions dodge the gate
        # (review F-04).
        deleted_code = "--- a/pricebook.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\n"
        added_code = "--- /dev/null\n+++ b/pricebook.py\n@@ -0,0 +1 @@\n+new\n"
        deleted_docs = "--- a/README.md\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            for name, diff, expect_missing in (
                ("code", code_diff, True), ("docs", docs_diff, False),
                ("deleted-code", deleted_code, True),
                ("added-code", added_code, True),
                ("deleted-docs", deleted_docs, False),
            ):
                path = Path(temp_dir) / f"{name}.diff"
                path.write_text(diff, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(script), "-", "--diff", str(path)],
                    input="Report with no gate lines at all.",
                    capture_output=True, text=True, timeout=30,
                )
                if expect_missing:
                    self.assertEqual(result.returncode, 1, name)
                    self.assertIn("MISSING INTENT", result.stdout, name)
                    self.assertIn("derived from --diff", result.stdout, name)
                else:
                    self.assertEqual(result.returncode, 0, name)

    def test_brief_carries_stop_defaults_and_auth_provenance(self) -> None:
        for path in (
            ".claude/skills/baton-dispatch/references/briefs-and-stops.md",
            ".codex/skills/leaf-dispatch/SKILL.md",
        ):
            body = read(path)
            self.assertIn("3 failed fix-verify", body, path)
            self.assertIn("fruitless lookups", body, path)
            self.assertIn("provenance-labelled direct quote", body, path)

    def test_no_write_roles_have_no_bash_surface(self) -> None:
        settings = json.loads(read(".claude/settings.json"))
        registered = [
            hook["command"]
            for matcher in settings["hooks"]["PreToolUse"]
            for hook in matcher["hooks"]
        ]
        self.assertFalse(
            any("readonly-bash.py" in command for command in registered)
        )
        self.assertFalse((ROOT / "main/claude/hooks/readonly-bash.py").exists())
        for role in NO_WRITE_ROLES:
            self.assertNotIn("Bash", frontmatter(f".claude/agents/{role}.md"))

    def test_bridge_brief_skeleton_carries_stops_and_authorization(self) -> None:
        body = read(".codex/scripts/bridge-brief")
        self.assertIn("Stops (append):", body)
        self.assertIn("Authorization (append", body)


if __name__ == "__main__":
    unittest.main()
