"""Leaf role contracts: roster invariants, twin parity, artifact gates."""
from support import *  # noqa: F401,F403


class AgentRosterTests(unittest.TestCase):
    def test_roster_matches_expected_roles(self) -> None:
        self.assertEqual(
            {p.stem for p in (ROOT / ".claude/agents").glob("*.md")},
            set(ROLES),
        )

    def test_every_role_owns_its_model_and_is_self_contained(self) -> None:
        for role in ROLES:
            meta = frontmatter(f".claude/agents/{role}.md")
            body = read(f".claude/agents/{role}.md")
            self.assertIn(f"name: {role}\n", meta)
            self.assertRegex(meta, r"(?m)^model:\s*\S+\s*$")
            self.assertLessEqual(len(body.splitlines()), 30, role)
            # Leaf roles never read orchestration docs or name the main contract.
            for forbidden in ("CLAUDE.md", "baton-dispatch", "provider-routing", "orchestration"):
                self.assertNotIn(forbidden, body, f"{role} leaks {forbidden}")

    def test_model_tiers_are_pinned(self) -> None:
        self.assertIn("model: sonnet", frontmatter(".claude/agents/Explore.md"))
        self.assertIn("model: sonnet", frontmatter(".claude/agents/mech-executor.md"))
        self.assertIn("model: sonnet", frontmatter(".claude/agents/executor.md"))
        for role in ("plan-verifier", "verifier",
                     "security-reviewer", "security-executor"):
            self.assertIn("model: opus", frontmatter(f".claude/agents/{role}.md"), role)

    PINNED_EFFORTS = {"Explore": "low", "mech-executor": "medium",
                      "executor": "high", "plan-verifier": "medium",
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
        for role in BASH_ROLES:
            meta = frontmatter(f".claude/agents/{role}.md")
            self.assertRegex(meta, r"(?m)^disallowedTools:.*\bAgent\b.*\bWorkflow\b")

    def test_explore_separates_recon_from_adversarial_review(self) -> None:
        for path in (".claude/agents/Explore.md", ".codex/agents/explore.toml"):
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
        self.assertIn("isolated worktree", outcome)
        self.assertIn("git status --short", outcome)
        self.assertIn("must be identical", outcome)

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
        # The clause names only the lines the role owes: mech has no INTENT/TWINS
        # template, and naming them made low-tier leaves improvise drifted lines.
        for path in (".claude/agents/mech-executor.md", ".codex/agents/mech-executor.toml"):
            body = read(path)
            self.assertNotIn("INTENT", body, path)
            self.assertNotIn("TWINS", body, path)

    def test_owed_line_audit_is_mechanized_in_both_qc_paths(self) -> None:
        # One shared implementation in .agents/scripts; both trees symlink it
        # (same relative depth in the repo and in HOME, synced with --links).
        shared = ROOT / ".agents/scripts/qc-gate-lines"
        self.assertTrue(shared.is_file(), shared)
        self.assertTrue(os.access(shared, os.X_OK), f"{shared} must be executable")
        for tree in (".claude", ".codex"):
            link = ROOT / tree / "scripts/qc-gate-lines"
            self.assertTrue(link.is_symlink(), f"{link} must be a symlink")
            self.assertEqual(
                os.readlink(link), "../../.agents/scripts/qc-gate-lines", link
            )
        qc_paths = (
            ".claude/skills/provider-routing/SKILL.md",
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
            "Explore": ["read-only leaf agent", "never delegate",
                        "file:line evidence", "genuinely new or redirected work"],
            "mech-executor": ["never delegate", "weaken", "stop and report",
                              "auth: user said"],
            "executor": ["never delegate", "intent: code does",
                         "stop and report"],
            "plan-verifier": ["ready", "revise", "replacement plan"],
            "verifier": ["confirmed", "refuted", "inconclusive",
                         "reproducible counterexample", "never fix"],
            "security-reviewer": ["abuse", "trust boundar"],
            "security-executor": ["weaken", "abuse", "intent: code does",
                                  "auth: user said"],
        }
        self.assertEqual(sorted(shared), sorted(r if r != "Explore" else "Explore"
                                                for r in ROLES))
        for role, clauses in shared.items():
            codex_role = "explore" if role == "Explore" else role
            claude = read(f".claude/agents/{role}.md").lower()
            codex = read(f".codex/agents/{codex_role}.toml").lower()
            for clause in clauses:
                self.assertIn(clause, claude, f"{role} (claude): {clause}")
                self.assertIn(clause, codex, f"{role} (codex): {clause}")

    def test_codex_writer_tomls_still_parse(self) -> None:
        for role in ("executor", "mech-executor", "security-executor"):
            agent = tomllib.loads(read(f".codex/agents/{role}.toml"))
            self.assertIn("INTENT" if role != "mech-executor" else "AUTH",
                          agent["developer_instructions"], role)

    def test_qc_fraud_checklist_in_both_main_qc_paths(self) -> None:
        for path in (".claude/skills/provider-routing/SKILL.md",
                     ".codex/skills/leaf-dispatch/SKILL.md"):
            body = " ".join(read(path).split())
            self.assertIn("false-completion frauds", body, path)
            self.assertIn("leftover leaf-created scratch files", body, path)
            self.assertIn("pre-existing dirty-worktree files are not debris", body, path)

    def test_brief_carries_stop_defaults_and_auth_provenance(self) -> None:
        for path in (
            ".claude/skills/baton-dispatch/references/briefs-and-stops.md",
            ".codex/skills/leaf-dispatch/SKILL.md",
        ):
            body = read(path)
            self.assertIn("3 failed fix-verify", body, path)
            self.assertIn("fruitless lookups", body, path)
            self.assertIn("provenance-labelled direct quote", body, path)

    def test_bridge_brief_skeleton_carries_stops_and_authorization(self) -> None:
        body = read(".codex/scripts/bridge-brief")
        self.assertIn("Stops (append):", body)
        self.assertIn("Authorization (append", body)


if __name__ == "__main__":
    unittest.main()
