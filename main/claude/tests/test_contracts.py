"""Resident contracts and skills: Claude, Codex bundle, doc budgets."""
from support import *  # noqa: F401,F403


# Each provider's always-loaded contract. One source for the two tests that
# budget it: the per-document ceiling and the resident-layer total (contract
# plus skill metadata), which must not be able to drift apart.
RESIDENT_CONTRACT_BUDGETS = {
    "claude": (".claude/CLAUDE.contract.md", 520),
    "codex": (".codex/AGENTS.contract.md", 540),
}


class ClaudeContractTests(unittest.TestCase):
    def test_claude_md_is_slim_and_outcome_first(self) -> None:
        policy = read(".claude/CLAUDE.contract.md")
        self.assertLessEqual(len(policy.splitlines()), 40)
        for phrase in (
            "Lead with the outcome",
            "preserve dirty worktrees",
            "Direct execution is the default",
            "## Main session only — orchestration",
            "DECISION: <what and why>",
        ):
            self.assertIn(phrase, policy)

    def test_claude_md_does_not_restate_the_harness_system_prompt(self) -> None:
        """Claude Code already states these; a second copy is not free.

        Anthropic's context-engineering guidance for the Claude 5 generation cut
        most of Claude Code's own system prompt because overlapping directives
        make the model spend reasoning reconciling them, and OpenAI's GPT-5.6
        guidance reports that repeating approval language makes a model ask
        permission for safe, expected actions. Each phrase below is carried by
        the harness prompt in equivalent or stronger form, so this contract must
        not carry it again.

        Note this applies to the Claude Code CLI only: the Codex contract and
        the app prompts face thinner host prompts and keep their own authority
        boundary. A 2026-07-31 audit briefly called that claim false, on the
        strength of one Codex rollout; measuring all 91 put it back, because
        the Codex *subagent* prompt — 47 of the 50 sessions on cli >= 0.145.0 —
        carries none of the autonomy or worktree language the top-level one
        does. See `CodexContractRestatementTests`.

        The Claude side of that audit has no equivalent evidence: Claude Code
        records its system prompt nowhere, so whether a Claude subagent
        receives the phrases banned below is currently unfalsifiable. Treat
        this list as the weaker-evidenced of the two.
        """
        policy = read(".claude/CLAUDE.contract.md")
        for restated in (
            "Infer low-risk ambiguity",
            "different answers materially change the result",
            "require explicit authority",
            "report failed or skipped checks exactly",
            "Do not add speculative features",
        ):
            self.assertNotIn(restated, policy)

    def test_dispatch_reporting_and_leaf_boundary(self) -> None:
        # The resident contract keeps the record names and the leaf boundary;
        # the field-level template lives in baton-dispatch (single source,
        # mirroring the Codex leaf-dispatch pattern).
        policy = read(".claude/CLAUDE.contract.md")
        self.assertIn("[LEAF_DISPATCH]", policy)
        self.assertIn("[LEAF_RESULT]", policy)
        self.assertIn("Never brief a subagent to delegate further", policy)
        self.assertIn("agent-to-agent briefs stay in precise, concise English", policy)
        skill = read(".claude/skills/baton-dispatch/SKILL.md")
        self.assertIn("dispatch_id=<id>", skill)
        for field in ("task=<label>", "role=<role>", "class=<class>",
                      "request_source=<request_source>", "route=<profile>/<provider>/<model>/<effort>",
                      "ledger=<logged|skipped(reason)>"):
            self.assertIn(field, skill)

    def test_effort_is_capped_at_high(self) -> None:
        for role in ROLES:
            self.assertNotIn("xhigh", frontmatter(f".claude/agents/{role}.md"), role)
        for path in (
            ".claude/skills/provider-routing/SKILL.md",
            ".codex/AGENTS.contract.md",
            ".codex/config.merge.toml",
        ):
            text = read(path)
            for sanctioned in ("no role or bridge call uses xhigh",
                               "Fable at medium\u2013xhigh",
                               "raise effort to xhigh"):
                text = text.replace(sanctioned, "")
            self.assertNotIn("xhigh", text, path)

    def test_claude_md_delegates_detail_to_skills(self) -> None:
        policy = read(".claude/CLAUDE.contract.md")
        for skill in ("baton-dispatch", "provider-routing", "headroom-protocol"):
            self.assertIn(skill, policy)
        # Routing detail and the version gate live in skills / the runtime-guard hook,
        # not inline in the resident contract.
        for moved in (
            "Discovery → Plan → Approval",
            "gpt-5.6-sol",
            "H = Opus",
            "2.1.207",
        ):
            self.assertNotIn(moved, policy)

    def test_baton_dispatch_skill_carries_recon_result_collection(self) -> None:
        skill = read(".claude/skills/baton-dispatch/SKILL.md")
        brief = read(".claude/skills/baton-dispatch/references/briefs-and-stops.md")
        # Progressive disclosure: the contract's cost test answers the common
        # case ("stay in main") on its own, so this skill is loaded only once a
        # dispatch is actually going ahead. A "mandatory before every dispatch"
        # description would both re-state the contract and make a 900-word file
        # resident for decisions that resolve without it.
        baton_meta = frontmatter(".claude/skills/baton-dispatch/SKILL.md")
        self.assertIn("Load once a dispatch is going ahead", baton_meta)
        self.assertNotIn("Mandatory", baton_meta)
        # Cost test: high-tier pinned delegation saves no compute; payoff must beat overhead.
        self.assertIn("## Cost test", skill)
        self.assertIn("delegation saves no compute", skill)
        self.assertIn("clearly exceeds dispatch overhead", read(".claude/CLAUDE.contract.md"))
        self.assertIn("clearly exceeds\ndispatch overhead", read(".codex/skills/leaf-dispatch/SKILL.md"))
        self.assertIn("cablate/baton v0.1.1", skill)
        self.assertIn("scope fix `0ab4d2e`", skill)
        self.assertNotIn("pilotfish", skill.lower())
        self.assertIn("hard boundary", skill)
        self.assertNotIn("Discovery → Plan → Approval", skill)
        # A1: orchestrator-side recon result-collection.
        self.assertIn("final response is its deliverable", skill)
        self.assertIn("never relaunch", skill)
        self.assertIn("genuinely new or redirected work", skill)
        # A2: recon facts are unverified inputs.
        self.assertIn("unverified input", skill)
        # A3: uncollected worktree is lost work.
        self.assertIn("lost unless the integration owner harvests", brief)
        self.assertIn("excluded adjacent capabilities", brief)
        self.assertIn("approved boundary crossed", brief)
        self.assertIn("Known one-file fix", brief)
        self.assertIn("Role, task class, and scenario", brief)
        self.assertIn("`review`", brief)
        self.assertIn("semantic-seams", brief)
        self.assertIn("LEAF_DISPATCH", skill)
        self.assertIn("LEAF_RESULT", skill)

    def test_pilotfish_guardrails_are_backend_neutral_and_cross_surface(self) -> None:
        skill = read(".claude/skills/baton-dispatch/SKILL.md")
        brief = read(".claude/skills/baton-dispatch/references/briefs-and-stops.md")
        claude = read(".claude/CLAUDE.contract.md")
        codex = read(".codex/AGENTS.contract.md")
        triggers = read(
            ".claude/skills/provider-routing/references/verifier-triggers.md"
        )

        codex_dispatch = " ".join(read(".codex/skills/leaf-dispatch/SKILL.md").split())
        codex_policy = codex + "\n" + codex_dispatch
        for text in (skill, brief, codex_dispatch):
            self.assertIn("stable one-shot brief", text)
            self.assertIn("independent and the same shape", text)
            self.assertIn("per-item acceptance", text)
        self.assertIn("known root cause and remedy", skill)
        self.assertIn("known remedy", codex_policy)
        self.assertIn("not a numeric trigger", brief)
        self.assertIn("never use an item-count trigger", codex_policy)

        for text in (skill, triggers, codex_policy):
            self.assertIn("smallest coherent integration boundary", text)
            self.assertIn("intermediate evidence", text)
        for text in (triggers, codex_policy):
            self.assertIn("cross-language or FFI", text)
            self.assertIn("serialization or pre-aggregation", text)
        # Plan anti-churn moved from the resident Claude contract into the
        # mandatory-pre-dispatch baton skill (union assertion, like codex).
        claude_policy = claude + "\n" + skill
        for text in (claude_policy, codex_policy):
            self.assertIn("substantially unchanged Plan", text)
            self.assertIn("material revision or new evidence", text)
            self.assertRegex(text, r"silently (overrule|overriding)")

    def test_pilotfish_v134_readiness_and_discovery_are_cross_surface(self) -> None:
        claude_dispatch = read(".claude/skills/baton-dispatch/SKILL.md")
        codex_dispatch = read(".codex/skills/leaf-dispatch/SKILL.md")
        brief = read(".claude/skills/baton-dispatch/references/briefs-and-stops.md")
        claude_plan = read(".claude/agents/plan-verifier.md")
        codex_plan = tomllib.loads(
            read(".codex/agents/plan-verifier.toml"))["developer_instructions"]
        claude_security = read(".claude/agents/security-reviewer.md")
        codex_security = tomllib.loads(
            read(".codex/agents/security-reviewer.toml"))["developer_instructions"]

        for text in (claude_dispatch, codex_dispatch):
            for phrase in (
                "program envelope",
                "next executable slice",
                "readiness-unit ID",
                "first readiness review",
                "after two automatic revisions",
                "Blocker",
                "Minimum revision",
                "Acceptance check",
            ):
                self.assertIn(phrase, text)
        for text in (claude_dispatch, codex_dispatch, brief):
            self.assertIn("temporarily exclusive", text)
            self.assertIn("back-to-back", text)
            self.assertIn("cross-surface synthesis", text)
        for text in (claude_plan, codex_plan):
            self.assertIn("stable readiness-unit ID", text)
            self.assertIn("READY", text)
            self.assertIn("with no other text", text)
            for field in (
                "Blocker:",
                "Evidence:",
                "Minimum revision:",
                "Acceptance check:",
            ):
                self.assertIn(field, text)
            self.assertIn("security-reviewer", text)
            self.assertIn("disposition", text)
        for text in (claude_security, codex_security):
            self.assertIn("stable ID", text)
            self.assertIn("affected Plan", text)
            self.assertIn("first readiness review", text)

    def test_provider_routing_owns_model_and_fallback_policy(self) -> None:
        skill = read(".claude/skills/provider-routing/SKILL.md")
        for phrase in (
            "omit invocation-level `model`",
            "H** = Opus/high or Fable/low",
            "X** = Opus/high or Fable at medium\u2013xhigh",
            "one cross-provider hop measured from the task's origin",
            "A fallback provider cannot route back",
            "one bounded retry",
            *(f"`{option}`" for option in DISPATCH_OPTIONS),
            "never two writers on the same artifacts",
            "Security keeps its capability split on either provider",
            "never include Fable",
            f"`{CODEX_BRIDGE}`",
            "--surface claude-bridge",
            "--model <model>`",
            "--effort <effort>`",
            "single source of truth for Codex bridge model and effort",
            "quality-guarded` only for high-risk, high-impact, or highly uncertain work",
            "write-capable by default",
            "explicitly prohibit writes",
            "`plan-verifier` returns READY/REVISE",
            "`verifier` returns CONFIRMED/REFUTED",
            "Do not stack gates over the same failure surface",
            "Dual-provider",
            "profiles are **deployment presets**, not per-dispatch routes",
            "updates all pins transactionally",
            f"invoked from Claude through the `{CODEX_BRIDGE}` bridge",
            "cost per acceptable outcome",
            "External indices are priors only",
        ):
            self.assertIn(phrase, skill)
        self.assertIn("${CODEX_HOME:-$HOME/.codex}/scripts/model-routing", skill)
        self.assertNotIn("--model gpt-5.6-sol", skill)

    def test_dispatch_skills_have_non_overlapping_ownership(self) -> None:
        baton = read(".claude/skills/baton-dispatch/SKILL.md")
        provider = read(".claude/skills/provider-routing/SKILL.md")
        leaf = read(".codex/skills/leaf-dispatch/SKILL.md")
        leaf_flat = " ".join(leaf.split())

        self.assertIn(
            "owns dispatch shape, grouping, briefs, collection, QC, and fixed records",
            baton,
        )
        self.assertIn("does not choose a provider/model", baton)
        self.assertIn(
            "Own provider/model/role selection, bridge resolution, "
            "cross-provider fallback, and verifier eligibility",
            provider,
        )
        self.assertIn("Record formats and QC mechanics stay in `baton-dispatch`", provider)
        self.assertNotIn("qc-gate-lines", provider)
        self.assertNotIn("[LEAF_DISPATCH]", provider)
        self.assertIn("Own Codex dispatch", leaf_flat)
        self.assertIn("do not select main model", leaf_flat)


class CodexContractRestatementTests(unittest.TestCase):
    """Why the Codex contract keeps clauses the Claude contract may not.

    The 2026-07-31 vendor-restatement audit deleted three of these, then a
    re-review put them back. Both passes read the same provider-recorded
    evidence — Codex writes its host prompt into `session_meta.base_instructions`
    of every rollout — but the first pass read *one* rollout. There are eight
    distinct prompts across 91 local rollouts, and the one it happened to read
    is the only variant carrying both the "File editing constraints" and
    "Destructive Actions" sections, so it maximised apparent vendor coverage.

    The axis is session kind, not CLI version. On cli >= 0.145.0:

        kind        n     autonomy   no-ask-scoped   dirty-worktree
        top-level   3        3/3          3/3             3/3
        subagent   47        0/47         0/47            0/47

    Codex delivers this contract to subagents as instructions - the rollout
    carries it as a `role: user` message headed `# AGENTS.md instructions` and
    mirrors it in `world_state.agents_md` - so a clause the subagent prompt
    omits has no other source. Deleting these removed the only statement of
    "the user's uncommitted work is theirs; preserve it" from every current
    subagent session, which is the half of the fleet that writes files.

    The rule this yields: judge a restatement against the *thinnest* host
    prompt any consumer of the contract runs under, never against a sampled
    one. The Claude side of the audit cannot be run at all - Claude Code
    records its system prompt nowhere, so the same sampling error there is
    currently unfalsifiable.
    """

    #: Present in the top-level Codex prompt, absent from every current
    #: subagent prompt, and the contract is loaded by both.
    SUBAGENT_UNCOVERED = (
        "preserve dirty worktrees and unrelated user work",
        "need no approval",
        "inspect and report",
    )

    def test_the_vendor_census_covers_every_justified_clause(self) -> None:
        """The measurement behind these decisions has to be re-runnable.

        The numbers above are a snapshot of one machine's rollouts. Left as
        prose they rot silently, and the audit that produced them was already
        re-derived once by hand and got it wrong. `scripts/codex-prompt-census.py`
        regenerates them on demand; this fails if a clause is justified here
        that the census does not measure, or vice versa, so the tool and the
        reasoning cannot drift apart.

        The census has no `--check` mode on purpose: its input is machine-local
        and expected to move, so a pinned snapshot would fail for everyone who
        is not the author. It is evidence for a human decision, not a gate.
        """
        import importlib.util

        script = ROOT / "scripts/codex-prompt-census.py"
        self.assertTrue(script.is_file(), script)
        spec = importlib.util.spec_from_file_location("codex_prompt_census", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        measured = {clause for _, clause, _ in module.CONTRACT_CLAUSES}
        justified = set(self.SUBAGENT_UNCOVERED) | {"require explicit authority"}
        self.assertEqual(
            justified, measured,
            "every clause kept or dropped on vendor-coverage grounds must be a "
            "column in the census, so the claim can be rechecked by running it")
        # And the census must still be reading the vendor's words, not ours:
        # a rollout for work in this repo quotes the contract everywhere else.
        self.assertTrue(module.OUR_MARKERS, "circularity check was removed")

    def test_clauses_the_subagent_prompt_does_not_carry_stay_in_the_contract(self) -> None:
        policy = read(".codex/AGENTS.contract.md")
        for clause in self.SUBAGENT_UNCOVERED:
            self.assertIn(
                clause, policy,
                f"{clause!r} was removed as a vendor restatement, but the "
                "Codex subagent prompt does not restate it (0/47 on cli "
                ">= 0.145.0) and subagents receive this contract")

    def test_the_authority_sentence_is_kept_on_purpose(self) -> None:
        """The one clause whose deletion the audit considered and declined.

        Unlike the three above, "# Destructive Actions" *is* in the subagent
        prompt (73/77), so this sentence really is a restatement. It stays
        anyway, because the failure directions are not symmetric: if the vendor
        drops that section, an over-cautious Codex is recoverable and one
        acting destructively without authority is not. A safety clause is not
        worth ~35 words of savings when the tail risk has that shape.
        """
        policy = read(".codex/AGENTS.contract.md")
        self.assertIn("require explicit authority", policy)


class CodexBundleTests(unittest.TestCase):
    def test_agents_md_mirrors_the_main_only_boundary(self) -> None:
        agents = read(".codex/AGENTS.contract.md")
        for phrase in (
            "Main task only — orchestration",
            "Direct execution is the default",
            "not request bullets",
            "one unknown bug's diagnosis",
            "Collect the finished subagent response",
            "hard boundary",
            "### Independent verifier",
            "Subagents use their own role contract",
            "Report only outcome",
            # Same progressive-disclosure rule as baton-dispatch on the Claude
            # side: the contract's cost test resolves the common case by itself.
            "Once a dispatch is going ahead, load the `leaf-dispatch` skill",
        ):
            self.assertIn(phrase, agents)
        self.assertNotIn("Discovery → Plan → Approval", agents)

    def test_dispatch_skill_metadata_triggers_only_after_the_decision(self) -> None:
        """Both providers pay the body only once a dispatch is going ahead.

        Skill metadata is resident on every turn; the body is not. That trade
        only pays if the description does not fire on "should I delegate?" —
        the question the resident contract answers by itself, usually with
        "no". The Codex description used to say both things at once (`Load
        before every leaf dispatch decision`, with 「要不要派」 as a trigger)
        while its own body and contract said the decision comes first, so
        asking whether to delegate loaded a ~1000-word file to decide not to.
        """
        for path in (".claude/skills/baton-dispatch/SKILL.md",
                     ".codex/skills/leaf-dispatch/SKILL.md"):
            meta = frontmatter(path)
            self.assertIn("Load once a dispatch is going ahead", meta, path)
            for pre_decision in ("before every leaf dispatch decision",
                                 "任何 leaf 派工前", "要不要派", "Mandatory"):
                self.assertNotIn(pre_decision, meta, path)

    def test_codex_dispatch_detail_lives_in_leaf_dispatch_skill(self) -> None:
        skill = " ".join(read(".codex/skills/leaf-dispatch/SKILL.md").split())
        self.assertIn("dispatch_id=<id>", skill)
        for phrase in (
            "request_source=codex",
            "[LEAF_DISPATCH]",
            "[LEAF_RESULT]",
            "false-completion frauds",
            "3 failed fix-verify",
            "fruitless lookups",
            "provenance-labelled direct quote",
            "at most one outcome verifier per top-level task",
            "smallest coherent integration boundary",
        ):
            self.assertIn(phrase, skill)
        # Detail moved out of the resident contract stays out.
        agents = read(".codex/AGENTS.contract.md")
        self.assertNotIn("false-completion frauds", agents)
        self.assertNotIn("3 failed fix-verify cycles", agents)

    def test_codex_bundle_avoids_claude_routing_vocabulary(self) -> None:
        # The Codex contract must not carry Claude-specific model routing.
        lowered = read(".codex/AGENTS.contract.md").lower()
        for forbidden in ("fable", "opus", "dispatch gpt +", "dispatch claude"):
            self.assertNotIn(forbidden, lowered)
        # The ownership invariant must stay resident; the routing detail that
        # states it may live in either the contract or the on-demand skill, so
        # assert the union — otherwise moving a line between them reads as
        # deleting it.
        self.assertIn("The user owns the Codex GPT model", read(".codex/AGENTS.contract.md"))
        self.assertIn("GPT-5.6 Sol/high",
                      read(".codex/AGENTS.contract.md")
                      + read(".codex/skills/leaf-dispatch/SKILL.md"))

    def test_config_merge_and_verifier_are_leaf_bounded(self) -> None:
        config = tomllib.loads(read(".codex/config.merge.toml"))
        self.assertEqual(config["agents"]["max_depth"], 1)
        self.assertEqual(config["agents"]["max_threads"], 4)
        self.assertEqual(
            config["agents"]["verifier"]["config_file"], "./agents/verifier.toml"
        )
        verifier = tomllib.loads(read(".codex/agents/verifier.toml"))
        self.assertEqual(verifier["sandbox_mode"], "read-only")
        # Codex role files stay reusable; the per-dispatch resolver passes effort.
        self.assertNotIn("model_reasoning_effort", verifier)
        self.assertIn("routine low-risk work", verifier["description"])

    def test_every_leaf_role_has_a_codex_counterpart(self) -> None:
        # Claude role -> codex agent file (same lowercase spelling since the
        # 2026-07-23 rename).
        counterparts = {
            "explore": "explore",
            "plan-verifier": "plan-verifier",
            "security-reviewer": "security-reviewer",
            "mech-executor": "mech-executor",
            "executor": "executor",
            "verifier": "verifier",
            "security-executor": "security-executor",
        }
        config = tomllib.loads(read(".codex/config.merge.toml"))
        read_only = NO_WRITE_ROLES
        for claude_role, codex_name in counterparts.items():
            path = f".codex/agents/{codex_name}.toml"
            agent = tomllib.loads(read(path))
            self.assertEqual(agent["name"], codex_name, path)
            # Routing profiles are selected per dispatch; role files stay reusable.
            self.assertNotIn("model", agent, path)
            self.assertNotIn("model_reasoning_effort", agent, path)
            expected_sandbox = "read-only" if codex_name in read_only else "workspace-write"
            self.assertEqual(agent["sandbox_mode"], expected_sandbox, path)
            self.assertRegex(agent["developer_instructions"].lower(), r"(never|do not) delegate", path)
            # Same ungameable unit as the Claude twin's body budget: a role
            # that outgrows it on one provider only would drift silently.
            self.assertLessEqual(
                word_count(agent["developer_instructions"]), ROLE_BODY_BUDGET, path)
            self.assertEqual(
                config["agents"][codex_name]["config_file"],
                f"./agents/{codex_name}.toml",
                codex_name,
            )

    def test_model_routing_profiles_are_complete_and_dispatchable(self) -> None:
        routing = tomllib.loads(read(".codex/model-routing.toml"))
        self.assertEqual(routing["version"], 3)
        self.assertEqual(
            routing["selection"],
            {
                "default": "balanced",
                "fast": "fast",
                "quality_guarded": "quality_guarded",
                "high_risk": "quality_guarded",
            },
        )
        self.assertEqual(
            set(routing["profiles"]),
            {"balanced", "fast", "quality_guarded"},
        )
        self.assertEqual(routing["revision_policy"], {
            "days": 90,
            "min_samples": 10,
            "half_life_days": 45.0,
            "prefer_probability": 0.90,
            "cohort_fields": ["role", "task_class"],
            "excluded_task_classes": ["smoke", "other"],
        })
        self.assertEqual(
            routing["revision_policy"],
            tomllib.loads(read(".claude/model-routing.toml"))["revision_policy"],
        )
        required_roles = {"main", *CODEX_ROLES}
        role_tiers = routing["quality_floor"]["roles"]
        application = routing["route_application"]["roles"]
        approved = routing["quality_floor"]["approved_routes"]
        self.assertEqual(set(role_tiers), required_roles)
        self.assertEqual(set(application), required_roles)
        self.assertEqual(application["main"], "session_start_recommendation")
        for role in CODEX_ROLES:
            self.assertEqual(application[role], "dispatch_override", role)
        for profile_name, profile in routing["profiles"].items():
            self.assertEqual(set(profile["roles"]), required_roles, profile_name)
            for role, route in profile["roles"].items():
                model = routing["models"][route["model"]]
                delivery = model["availability"]["native_leaf_override"]
                self.assertIn(delivery, {"spawn_argument", "agent_config"})
                if role != "main" and delivery == "agent_config":
                    self.assertIn("agent_type", route, f"{profile_name}/{role}")
                self.assertIn(route["effort"], model["efforts"], f"{profile_name}/{role}")
                self.assertIn(
                    f"{route['model']}/{route['effort']}",
                    approved[role_tiers[role]],
                    f"{profile_name}/{role} falls below its quality floor",
                )
                self.assertTrue(route["reason"], f"{profile_name}/{role}")
                self.assertNotEqual(route["model"], "gpt-5.6-luna")

        luna_availability = routing["models"]["gpt-5.6-luna"]["availability"]
        self.assertEqual(
            luna_availability,
            {
                "subscription": "documented",
                "main_selector": "documented",
                "native_leaf_override": "agent_config",
                "claude_bridge_override": "configured",
            },
        )
        self.assertIn("smoke-tested", routing["models"]["gpt-5.6-luna"]["evidence"]["native_leaf"])
        self.assertIn("smoke-tested", routing["models"]["gpt-5.6-luna"]["evidence"]["claude_bridge"])
        self.assertNotIn("surface_overrides", routing)
        for model in routing["models"].values():
            self.assertEqual(
                set(model["efforts"]), {"low", "medium", "high", "xhigh", "max"}
            )
        self.assertAlmostEqual(
            routing["models"]["gpt-5.6-terra"]["efforts"]["max"]
            ["cost_usd_per_index_task"],
            0.82461,
        )
        self.assertAlmostEqual(
            routing["models"]["gpt-5.6-sol"]["efforts"]["high"]
            ["output_tokens_per_index_task"],
            6690.3086,
        )

    def test_model_routing_cli_validates_and_resolves_quality_first_priority(self) -> None:
        script = ROOT / "main/codex/scripts/model-routing"
        self.assertTrue(os.access(script, os.X_OK))
        validated = subprocess.run(
            [str(script), "validate"], check=True, capture_output=True, text=True,
        )
        self.assertIn("valid: 3 profiles", validated.stdout)
        resolved = subprocess.run(
            [str(script), "resolve", "--priority", "fast",
             "--role", "executor"],
            check=True, capture_output=True, text=True,
        )
        route = json.loads(resolved.stdout)
        self.assertEqual(route["profile"], "fast")
        self.assertEqual(route["surface"], "native-leaf")
        self.assertEqual(route["application"], "dispatch_override")
        self.assertEqual(route["quality_tier"], "judgment")
        self.assertEqual(route["model"], "gpt-5.6-sol")
        self.assertEqual(route["effort"], "medium")
        high_risk = subprocess.run(
            [str(script), "resolve", "--priority", "high-risk",
             "--role", "executor"],
            check=True, capture_output=True, text=True,
        )
        high_risk_route = json.loads(high_risk.stdout)
        self.assertEqual(high_risk_route["profile"], "quality_guarded")
        fast_support = subprocess.run(
            [str(script), "resolve", "--priority", "fast",
             "--role", "explore"],
            check=True, capture_output=True, text=True,
        )
        fast_support_route = json.loads(fast_support.stdout)
        self.assertEqual(fast_support_route["model"], "gpt-5.6-terra")
        self.assertEqual(fast_support_route["effort"], "low")
        self.assertEqual(fast_support_route["invocation"], {
            "agent_type": "explore",
            "fork_turns": "none",
            "model_delivery": "spawn_argument",
            "pass_model_override": True,
        })
        guarded = subprocess.run(
            [str(script), "resolve", "--priority", "quality-guarded",
             "--role", "explore"],
            check=True, capture_output=True, text=True,
        )
        guarded_route = json.loads(guarded.stdout)
        self.assertEqual(guarded_route["profile"], "quality_guarded")
        self.assertEqual(guarded_route["model"], "gpt-5.6-sol")
        self.assertEqual(guarded_route["effort"], "low")

        bridge = subprocess.run(
            [str(script), "resolve", "--surface", "claude-bridge",
             "--priority", "fast", "--role", "explore"],
            check=True, capture_output=True, text=True,
        )
        bridge_route = json.loads(bridge.stdout)
        self.assertEqual(bridge_route["surface"], "claude-bridge")
        self.assertEqual(bridge_route["model"], "gpt-5.6-terra")
        self.assertEqual(bridge_route["effort"], "low")
        self.assertEqual(
            bridge_route["invocation"]["model_delivery"],
            "bridge_argument",
        )

        original = read(".codex/model-routing.toml")
        invalid = original.replace(
            '[profiles.fast.roles.executor]\nmodel = "gpt-5.6-sol"',
            '[profiles.fast.roles.executor]\nmodel = "gpt-5.6-terra"',
            1,
        )
        self.assertNotEqual(invalid, original)
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_config = Path(temp_dir) / "model-routing.toml"
            invalid_config.write_text(invalid, encoding="utf-8")
            rejected = subprocess.run(
                [str(script), "--config", str(invalid_config), "validate"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("falls below quality tier judgment", rejected.stderr)

        slow_fast = original.replace(
            '[profiles.fast.roles.explore]\nmodel = "gpt-5.6-terra"',
            '[profiles.fast.roles.explore]\nmodel = "gpt-5.6-sol"',
            1,
        )
        self.assertNotEqual(slow_fast, original)
        with tempfile.TemporaryDirectory() as temp_dir:
            slow_config = Path(temp_dir) / "model-routing.toml"
            slow_config.write_text(slow_fast, encoding="utf-8")
            rejected_fast = subprocess.run(
                [str(script), "--config", str(slow_config), "validate"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(rejected_fast.returncode, 0)
        self.assertIn("is not optimal for decode_minutes_per_index_task",
                      rejected_fast.stderr)

        unavailable_bridge = original.replace(
            'claude_bridge_override = "configured"',
            'claude_bridge_override = "unverified"',
            1,
        )
        self.assertNotEqual(unavailable_bridge, original)
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_config = Path(temp_dir) / "model-routing.toml"
            bridge_config.write_text(unavailable_bridge, encoding="utf-8")
            rejected_bridge = subprocess.run(
                [str(script), "--config", str(bridge_config), "validate"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(rejected_bridge.returncode, 0)
        self.assertIn("uses model unavailable to claude-bridge",
                      rejected_bridge.stderr)

        with tempfile.TemporaryDirectory() as temp_dir:
            malformed_config = Path(temp_dir) / "model-routing.toml"
            malformed_config.write_text("[broken", encoding="utf-8")
            malformed = subprocess.run(
                [str(script), "--config", str(malformed_config), "validate"],
                capture_output=True, text=True,
            )
        self.assertEqual(malformed.returncode, 2)
        self.assertIn("ERROR: cannot load routing config", malformed.stderr)
        self.assertNotIn("Traceback", malformed.stderr)

    def test_model_routing_bundle_is_documented_and_synced(self) -> None:
        readme = read(".codex/README.md")
        deploy = read(".codex/DEPLOY.md")
        managed = set(deployment_manifest())
        for artifact in ("model-routing.toml", "scripts/model-routing"):
            self.assertIn(artifact, readme)
            self.assertIn(artifact, deploy)
        self.assertIn(("main/codex/model-routing.toml", ".codex/model-routing.toml"), managed)
        self.assertIn(("main/codex/scripts", ".codex/scripts"), managed)
        agents = read(".codex/AGENTS.contract.md")
        # The resolver path is operational detail and lives wherever the
        # dispatch mechanics live; only the "routes do not switch a running
        # task" invariant has to be resident. Assert the union so relocating
        # the command does not read as dropping it.
        self.assertIn("${CODEX_HOME:-$HOME/.codex}/scripts/model-routing",
                      agents + read(".codex/skills/leaf-dispatch/SKILL.md"))
        self.assertIn("session-start recommendations", agents)

    def test_codex_dispatch_reporting_matches_claude(self) -> None:
        agents = read(".codex/AGENTS.contract.md")
        self.assertIn("[LEAF_DISPATCH]", agents)
        self.assertIn("[LEAF_RESULT]", agents)
        self.assertIn("request_source=codex", agents)
        self.assertIn("Never brief a subagent to delegate further", agents)
        skill = read(".codex/skills/leaf-dispatch/SKILL.md")
        self.assertIn("ledger=<logged|skipped(reason)>", skill)
        self.assertIn("quality-check it against the brief", skill)

    def test_deploy_and_analysis_preserve_machine_state(self) -> None:
        deploy = read(".codex/DEPLOY.md")
        analysis = read(".codex/ANALYSIS.md")
        for phrase in (
            "## One-shot Codex command",
            # The rule is now enforced by merge-toml rather than by asking
            # a human to be careful, so assert the scope guarantee itself.
            "never replaces `config.toml`",
            "writes only `[agents]` and `[agents.*]`",
            "Credentials and login",
            "Authentication only",
            "Keep approval enabled",
        ):
            self.assertIn(phrase, deploy)
        self.assertNotIn("/Users/", deploy)
        self.assertIn("not automatic deployment", analysis)
        self.assertIn("Git is the cross-machine source of truth", analysis)


class AppPromptSurfaceTests(unittest.TestCase):
    def test_app_prompts_keep_surface_ownership_and_action_boundaries(self) -> None:
        claude_chat = read(".claude/prompts/claude-app-profile.md")
        cowork = read(".claude/prompts/cowork-global-instructions.md")
        chatgpt = read(".codex/prompts/custom-instructions.md")

        self.assertIn("Settings > Instructions for Claude", claude_chat)
        self.assertIn("Settings > Cowork > Global instructions", cowork)
        self.assertIn("Settings > Personalization > Custom instructions", chatgpt)
        self.assertIn("Applies to Chat and Work", chatgpt)
        self.assertIn("$CODEX_HOME/AGENTS.md", chatgpt)

        for prompt in (claude_chat, cowork, chatgpt):
            self.assertIn("explicit authority", prompt)
        self.assertIn("reopen each produced file", cowork)
        self.assertIn("reopen the outputs", chatgpt)
        self.assertIn("produced artifacts and where to find them", cowork)

    def test_app_prompt_sources_are_managed_without_replacing_codex_contract(self) -> None:
        managed = set(deployment_manifest())
        self.assertIn(("main/claude/prompts", ".claude/prompts"), managed)
        self.assertIn(("main/codex/prompts", ".codex/prompts"), managed)

        readme = read(".codex/README.md")
        analysis = read(".codex/ANALYSIS.md")
        deploy = read(".codex/DEPLOY.md")
        self.assertIn("ChatGPT Chat／Work", readme)
        self.assertIn("`AGENTS.contract.md`", readme)
        self.assertIn("ChatGPT Chat and Work", analysis)
        self.assertIn("ChatGPT Chat and Work Personalization", deploy)
        self.assertIn("Codex uses global `AGENTS.md` for personal instructions", deploy)


class DocumentationBudgetTests(unittest.TestCase):
    def test_prompt_surface_census_is_current(self) -> None:
        snapshot = ROOT / "docs/research/prompt-surface-census.json"
        command = [
            str(ROOT / "main/.agents/scripts/python3-run"),
            str(ROOT / "scripts/prompt-surface-census.py"),
            "--check",
            str(snapshot),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

        census = json.loads(snapshot.read_text(encoding="utf-8"))
        self.assertEqual(census["schema"], 1)
        self.assertEqual(set(census["providers"]), {"claude", "codex"})
        managed_sources = {source for source, _target in deployment_manifest()}
        self.assertNotIn("scripts/prompt-surface-census.py", managed_sources)
        for provider, skills_dir in (
            ("claude", "main/claude/skills"),
            ("codex", "main/codex/skills"),
        ):
            expected_skills = {
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / skills_dir).glob("*/SKILL.md")
            }
            provider_layers = census["providers"][provider]
            resident_metadata = {
                record["path"]
                for record in provider_layers["resident"]
                if record.get("kind") == "skill-metadata"
            }
            metadata_records = [
                record
                for record in provider_layers["resident"]
                if record.get("kind") == "skill-metadata"
            ]
            dispatch_bodies = {
                record["path"]
                for record in provider_layers["dispatch"]
                if record.get("kind") == "skill-body"
            }
            self.assertEqual(resident_metadata, expected_skills)
            self.assertEqual(dispatch_bodies, expected_skills)
            self.assertTrue(
                all(record["words"] > 5 for record in metadata_records),
                f"{provider} skill descriptions must be fully counted",
            )
        for provider in ("claude", "codex"):
            self.assertEqual(
                set(census["providers"][provider]),
                {"resident", "dispatch", "roles"},
            )
            self.assertEqual(
                len(census["providers"][provider]["roles"]), len(ROLES)
            )
            for layer in ("resident", "dispatch", "roles"):
                total = census["totals"][provider][layer]
                self.assertGreater(total["bytes"], 0)
                self.assertGreater(total["words"], 0)
                self.assertRegex(total["payload_sha256"], r"^[0-9a-f]{64}$")

    def test_resident_skill_metadata_stays_within_budget(self) -> None:
        """Cap the resident layer at its real load unit, not at the snapshot.

        Every skill's name and description is loaded into every session, so a
        long description is a permanent per-session cost — the same cost the
        contract budgets above exist to control. The census measured it, but
        nothing capped it: a description could grow without limit and the suite
        stayed green as soon as someone regenerated the snapshot. So this reads
        the sources, not `prompt-surface-census.json`, and the resident total
        below is the contract budget plus this one.
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "prompt_surface_census", ROOT / "scripts/prompt-surface-census.py")
        census_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(census_module)
        census = census_module.build_census()

        # Per-provider sum of skill metadata, in the same CJK-aware words the
        # document budgets use. Raising either is a deliberate decision with a
        # reason, exactly like raising a document budget.
        # Claude carries one more skill than Codex (baton-dispatch and
        # provider-routing against the single leaf-dispatch).
        metadata_budgets = {"claude": 620, "codex": 540}
        # The widest legitimate description today is speak-human-tw at 176: it
        # states its triggers twice, in zh-TW and English, because it is the
        # one skill invoked by users in either language.
        per_skill_budget = 180
        for provider, budget in metadata_budgets.items():
            records = [record
                       for record in census["providers"][provider]["resident"]
                       if record.get("kind") == "skill-metadata"]
            self.assertTrue(records, provider)
            for record in records:
                self.assertLessEqual(
                    record["words"], per_skill_budget,
                    f"{record['path']}: resident skill metadata")
            self.assertLessEqual(
                sum(record["words"] for record in records), budget, provider)

        for provider, (contract, contract_budget) in RESIDENT_CONTRACT_BUDGETS.items():
            self.assertLessEqual(
                census["totals"][provider]["resident"]["words"],
                contract_budget + metadata_budgets[provider],
                f"{provider} resident layer ({contract} plus skill metadata)")

    def test_the_widest_description_keeps_every_trigger_it_pays_for(self) -> None:
        """A description is resident cost *and* the only routing surface.

        speak-human-tw is the largest always-resident description in the repo,
        which makes it the standing trim candidate — and trimming it is the one
        edit whose damage no test here can see, because whether a skill loads is
        decided by a model reading this text, not by anything mechanical.

        Written before any trim, deliberately (2026-07-30). A trim was measured
        and then dropped: the honest saving was 19 words, ~2% of the resident
        tier, against a recall risk nothing could measure at the time. So the
        lock landed first and the description was left alone until it is
        actually near its ceiling.

        `evals/traps/s10-skill-recall` was built afterwards to close that gap
        and carries the dropped trim as its arm-B surface. It is still a
        model-in-the-loop eval, not a check this suite can run: these
        assertions are the cheap layer, the trap is the expensive one, and
        neither replaces the other.

        Word budgets push one way and recall pushes the other. Both are
        asserted, so whenever a trim does happen it has to come out of genuine
        duplication rather than out of the tokens that make the skill load.
        """
        frontmatter_text = frontmatter(".agents/skills/speak-human-tw/SKILL.md")
        # Every phrasing a user is expected to invoke it by, in both languages.
        for trigger in ("去 AI 味", "說人話", "這段好 AI", "改自然一點",
                        "校對再發", "審查", "改寫",
                        "de-AI this text", "make it sound human",
                        "polish this zh-TW copy before publishing"):
            self.assertIn(trigger, frontmatter_text, f"lost trigger: {trigger}")
        # The document kinds are the recall surface for "look at this <thing>"
        # phrasings; dropping one silently stops the skill matching that ask.
        for kind in ("電子報", "社群貼文", "銷售頁", "文案", "客服信",
                     "簡報", "公告"):
            self.assertIn(kind, frontmatter_text, f"lost document kind: {kind}")
        # Exclusions are what stop it loading on work it would damage.
        for exclusion in ("逐字翻譯", "品牌", "事實查核", "設定檔",
                          "literal translation", "brand-voice mimicry",
                          "fact-checking", "code/log/config"):
            self.assertIn(exclusion, frontmatter_text,
                          f"lost exclusion: {exclusion}")

    def test_docs_stay_distilled(self) -> None:
        # Word budgets, not line budgets — a line count is gameable by long
        # lines; words track resident attention cost. Raising a budget is a
        # deliberate decision, not a mechanical bump.
        # Units are word_count() words: one per CJK character, one per other
        # non-space run — zh-TW prose pays the same attention tax as English.
        budgets = {
            ".claude/CLAUDE.contract.md": RESIDENT_CONTRACT_BUDGETS["claude"][1],
            # Root README owns the complete architecture overview and diagrams;
            # operational/research detail remains linked in docs/.
            # +30 (2026-07-25): alias generation check added to the mechanisms
            # table — a new guardrail belongs in that inventory, and the row is
            # already at the terseness of its neighbours.
            # +90 (2026-07-26): the accurate fail-closed gate set (four bounded
            # gates, not two) plus the architecture and hook-system pointers. A
            # guardrail the index does not list is a guardrail nobody verifies.
            # +15 (2026-07-29): the verifier-quota row said the gate refuses a
            # second verifier per task; it refuses one per prompt. The index
            # naming a stronger guarantee than the mechanism has is worse than
            # the words it saves.
            # +45 (2026-07-29): the commit-gate row claimed the gate resolves
            # every repo a command targets and stopped there. A limit that is
            # not written down reads as a guarantee, so the row now names the
            # class only the Git argv boundary can catch.
            # +40 (2026-07-30): a review reproduced `git -c core.hooksPath=...`
            # inside a wrapper, which no client-side hook survives. The row now
            # names that residue and the layer that closes it; the fifth gate
            # is also counted where the four were listed.
            "README.md": 2560,
            # +80 (2026-07-26): navigation and responsibility rows for the
            # dispatch-lifecycle doc. A navigation surface has to grow when the
            # thing it navigates to appears, or it stops being complete.
            # +60 (2026-07-26): the language-layering rule and its one
            # exception. An unstated convention cannot distinguish a
            # deliberate exception from drift, which is what a reviewer found.
            # +55 (2026-07-26): navigation and responsibility rows for the
            # hook-system concept doc.
            # +70 (2026-07-26): navigation and responsibility rows for the
            # top-down architecture overview, now the recommended entry point.
            # +20 (2026-07-26): nav row for the Fable 5 fallback research doc.
            # +100 (2026-07-28): the punctuation rule. Rule 6 fixed which
            # *language* each layer writes in but left the width of the marks
            # unstated, and the repo drifted into both conventions (481
            # half-width vs 1695 full-width CJK-adjacent marks). One stated
            # convention is what lets a reviewer call a mixed file drift
            # instead of taste.
            "docs/README.md": 1050,
            # Verification entry point for dispatch state and route evidence.
            # Cheaper here than in the resident contracts or the two skills it
            # ties together, both of which sit within ten words of their own
            # ceilings.
            # +250 (2026-07-28): readiness-unit state and live-discovery
            # ownership now have a verification entry point outside prompts.
            # +130 (2026-07-29): route attestation is now two paths, not one.
            # The Claude side gained its own evidence chain, and the tier list
            # gained the rule that decides which tiers move a route — the part
            # a reader needs before trusting any of the numbers downstream.
            # +10 (2026-07-29): what a real per-task quota would need (a stable
            # task id in the payload) and why there isn't one. A disclosed gap
            # that does not say what would close it reads as an oversight.
            # +260 (2026-07-30): the state table promised a carrier for every
            # state, but native Codex had none for launched or collected — a
            # forgotten outcome there was undetectable, and the omissions skew
            # toward the hard dispatches. The section names the carrier, the
            # commands, and what a dispatcher-written wrapper still cannot
            # close; the last part is why it is prose and not one table cell.
            "docs/dispatch-lifecycle.md": 2300,
            # The hook-system concept doc: fail-open/fail-closed semantics, the
            # per-event inventory, and why each gate is trustworthy. The
            # guardrail table in the README pointed at individual hooks but no
            # doc explained the system as a whole.
            # +100 (2026-07-29): the commit-gate row described how the text is
            # matched but not which repo the match is checked against, nor that
            # a program can commit with the word nowhere in the command. Both
            # are what a reader needs to know when the gate stays silent.
            # +200 (2026-07-29): the git-side pre-commit gate — its own row, and
            # what the two boundaries do and do not each cover. A second gate
            # documented only in the first one's caveat is a gate readers will
            # attribute the wrong guarantee to.
            # +130 (2026-07-30): the paragraph naming what a client-side gate
            # cannot close (`--no-verify`, `-c core.hooksPath=...`,
            # `commit-tree`, all hidable in a wrapper) and where it is closed
            # instead, plus what the installer does when another tool already
            # owns core.hooksPath. Both were reproduced by review before the
            # prose claimed otherwise.
            "docs/hook-system.md": 1730,
            # Top-down architecture spine: one diagram then a concise walk
            # through every layer, each pointing at its specialized doc. The
            # connective narrative the README (a repo landing page) and the
            # per-topic docs each lacked.
            "docs/architecture.md": 2000,
            # How to avoid Anthropic's Fable 5 -> Opus safety fallback while on
            # a Fable main session: dispatch flagging work to Opus-immune
            # leaves, keep main context clean, and turn auto-switch off as the
            # observable safety net. Distinct from the repo's own cross-provider
            # fallback, which the doc disambiguates.
            # +440 (2026-07-26): design notes for four unimplemented directions
            # (heuristic hook, payoff codification, routing disambiguation,
            # main-session audit gap), recorded with approach/principle/open-
            # questions for later evaluation rather than built now.
            "docs/fable-5-fallback.md": 2000,
            # +100 (2026-07-23): behavioral trap-eval method section added.
            # +310 (2026-07-26): both vendors published context-engineering
            # guidance in the same week and both name rule *contradiction* as a
            # failure mode distinct from dilution — the playbook had only the
            # dilution half. Everything that could be moved out was: the numbers,
            # the source-by-source comparison, and the repo audit live in the
            # research doc, and the repo-specific tool-description caveat lives
            # in contract-slimming's placement table. What is left is 13 lines of
            # reusable rule with no home elsewhere.
            "docs/harness-engineering.md": 2760,
            # +30 (2026-07-28): the deferred punctuation sweep as an open item.
            # A user-approved-but-deprioritized decision that lives only in a
            # chat log is indistinguishable from one nobody made.
            # +50 (2026-07-28): current-state rows for v1.3.4 readiness,
            # discovery ownership, prompt census, and deferred mech evidence.
            ".claude/plans/orchestration-plan.md": 1380,
            # -50 (2026-07-26): route resolution, priority selection, and
            # unavailability reporting moved to the on-demand `leaf-dispatch`,
            # where the invocation mechanics already lived. The ceiling drops
            # with the content — leaving it at 590 would just invite a refill,
            # and this file sat 2 words under it.
            ".codex/AGENTS.contract.md": RESIDENT_CONTRACT_BUDGETS["codex"][1],
            ".codex/ANALYSIS.md": 500,
            ".codex/DEPLOY.md": 550,
            # +90 (2026-07-23): record template and QC fraud checklist moved
            # in from the resident contract / provider-routing (net resident
            # payload down; skill is mandatory before every dispatch).
            # +150 (2026-07-28): v1.3.4 readiness-unit schema, security review
            # sequencing, and live-discovery ownership. These remain on-demand;
            # the census records their cost instead of charging resident turns.
            ".claude/skills/baton-dispatch/SKILL.md": 1130,
            # QC mechanics and fixed records belong to baton-dispatch; keep
            # provider-routing focused on route, fallback, and eligibility.
            ".claude/skills/provider-routing/SKILL.md": 1300,
            # +45 (2026-07-25): invocation mechanics (fork_turns, spawn_argument
            # vs agent_config) moved out of the always-resident Codex contract
            # into this on-demand skill. The resident side of that trade is
            # visible above: AGENTS.contract.md model-ownership dropped ~23
            # words while staying under its own ceiling.
            # +85 (2026-07-26): the receiving side of the trade above. Paid
            # once per dispatch instead of once per task.
            # +160 (2026-07-28): Claude-twin readiness, security sequencing,
            # and discovery ownership; still paid only when dispatch proceeds.
            # +65 (2026-07-30): the ledger section now has to say how a native
            # Codex dispatch stages its own launch and completion. Claude gets
            # that from a hook and pays nothing for it here; on Codex it is the
            # dispatcher's step, so the instruction has to reach the dispatcher.
            ".codex/skills/leaf-dispatch/SKILL.md": 1075,
            # The four below were unbudgeted until 2026-07-30: the ceiling
            # existed on the three files someone had remembered, not on the
            # tier, so the largest dispatch-time surface in the repo
            # (speak-human-tw) had no limit at all. Each is set at its measured
            # size plus ~2%, which is what the three above already are (100%,
            # 99%, 98% used). The number is not a researched threshold — the
            # repo's own sources say none is derivable
            # (docs/research/context-and-vendors.md) — it is a ratchet: growth
            # has to displace something or be argued for in the commit message.
            #
            # experience-ledger and speak-human-tw are one source each, shared
            # by both providers through a symlink; both deployed surfaces are
            # listed because both are what a session actually loads.
            ".claude/skills/experience-ledger/SKILL.md": 980,
            ".codex/skills/experience-ledger/SKILL.md": 980,
            # Largest dispatch-time body in the repo, and the one that states
            # its triggers twice (zh-TW and English) because either language
            # can invoke it. Trimming it is deliberately a separate task.
            ".claude/skills/speak-human-tw/SKILL.md": 2090,
            ".codex/skills/speak-human-tw/SKILL.md": 2090,
            # Claude's copies are thin pointers; Codex carries the procedure,
            # so the two sides of these two skills are genuinely different
            # files and get their own ceilings rather than a shared one.
            ".claude/skills/headroom-protocol/SKILL.md": 135,
            ".codex/skills/headroom-protocol/SKILL.md": 235,
            ".claude/skills/task-observer/SKILL.md": 145,
            ".codex/skills/task-observer/SKILL.md": 770,
        }
        self.assertEqual(
            {path for path in budgets if "/skills/" in path},
            deployed_skill_files(),
            "every deployed skill is budgeted or the ceiling is back to being "
            "whatever someone remembered to list")
        for path, limit in budgets.items():
            self.assertLessEqual(word_count(read(path)), limit, path)

        # The word unit counts a run of non-space text as one word, so a single
        # unbroken run — a giant URL, a minified block, a pasted payload — costs
        # one budget unit no matter how much context it actually occupies. Cap
        # the run length so the budget cannot be evaded that way. The longest
        # legitimate run in these files today is a 106-character markdown link.
        for path in budgets:
            longest = max(re.findall(r"\S+", read(path)), key=len)
            self.assertLessEqual(
                len(longest), MAX_UNBROKEN_RUN,
                f"{path}: {len(longest)}-character unbroken run evades the word "
                f"budget; break it up or link to it: {longest[:80]}")

    def test_root_readme_is_a_complete_navigation_surface(self) -> None:
        readme = read("README.md")
        self.assertEqual(readme.count("```mermaid"), 2)
        for phrase in (
            "配置與部署拓撲",
            "派工與資料回饋迴路",
            "Main 與七個 leaf roles",
            "Role、task class 與 scenario 分離",
            "Routing 語意",
            "結構化派工回報",
            "機制與護欄",
            "管理邊界",
            "docs/README.md",
        ):
            self.assertIn(phrase, readme)

    def test_documentation_navigation_links_resolve_locally(self) -> None:
        paths = [
            "README.md", "docs/README.md", "main/claude/README.md",
            "main/codex/README.md", "main/.agents/README.md",
        ]
        missing = []
        for path in paths:
            base = (ROOT / path).parent
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", read(path)):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                local = target.split("#", 1)[0]
                if local and not (base / local).resolve().exists():
                    missing.append(f"{path}: {target}")
        self.assertEqual(missing, [])

    def test_documented_baseline_matches_runtime_contract(self) -> None:
        plan = read(".claude/plans/orchestration-plan.md")
        readme = read("README.md")
        self.assertIn("Current as of 2026-07-28", plan)
        self.assertIn("MIT", readme)
        self.assertIn("Yuhuan", read("LICENSE"))
        self.assertIn("same-role, same-task-class", plan)
        self.assertNotIn("AR lead >=10pt", plan)

    def test_harness_engineering_keeps_role_boundaries_local(self) -> None:
        doc = read("docs/harness-engineering.md")
        research = read("docs/research/model-evidence.md")
        self.assertIn("main-only 段必須短", doc)
        self.assertIn("角色檔要自足", doc)
        self.assertIn("每個可接受成果的預期總成本", doc)
        self.assertIn("完整主張可反駁的最小整合邊界", doc)
        self.assertIn("stable brief", doc)
        self.assertIn("研究摘要不再複製容易過期的 route 表格", research)



if __name__ == '__main__':
    unittest.main()
