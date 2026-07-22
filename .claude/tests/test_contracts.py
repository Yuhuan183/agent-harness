"""Resident contracts and skills: Claude, Codex bundle, doc budgets."""
from support import *  # noqa: F401,F403


class ClaudeContractTests(unittest.TestCase):
    def test_claude_md_is_slim_and_outcome_first(self) -> None:
        policy = read(".claude/CLAUDE.contract.md")
        self.assertLessEqual(len(policy.splitlines()), 40)
        for phrase in (
            "Lead with the outcome",
            "Infer low-risk ambiguity",
            "different answers materially change the result",
            "preserve dirty worktrees",
            "require explicit authority",
            "Direct execution is the default",
            "## Main session only — orchestration",
        ):
            self.assertIn(phrase, policy)

    def test_dispatch_reporting_and_leaf_boundary(self) -> None:
        policy = read(".claude/CLAUDE.contract.md")
        self.assertIn("[LEAF_DISPATCH]", policy)
        self.assertIn("[LEAF_RESULT]", policy)
        for field in ("task=<label>", "role=<role>", "class=<class>",
                      "request_source=<request_source>", "route=<profile>/<provider>/<model>/<effort>",
                      "ledger=<logged|skipped(reason)>"):
            self.assertIn(field, policy)
        self.assertIn("Never brief a subagent to delegate further", policy)
        self.assertIn("agent-to-agent briefs stay in precise, concise English", policy)

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
            "H = Fable",
            "2.1.207",
        ):
            self.assertNotIn(moved, policy)

    def test_baton_dispatch_skill_carries_recon_result_collection(self) -> None:
        skill = read(".claude/skills/baton-dispatch/SKILL.md")
        brief = read(".claude/skills/baton-dispatch/references/briefs-and-stops.md")
        self.assertIn("Mandatory before every dispatch", frontmatter(".claude/skills/baton-dispatch/SKILL.md"))
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

    def test_pilotfish_v130_guardrails_are_backend_neutral_and_cross_surface(self) -> None:
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
            self.assertIn("cross-language or FFI", text)
            self.assertIn("serialization or pre-aggregation", text)
        for text in (skill, claude, codex_policy):
            self.assertIn("substantially unchanged Plan", text)
            self.assertIn("material revision or new evidence", text)
            self.assertRegex(text, r"silently (overrule|overriding)")

    def test_provider_routing_owns_model_and_fallback_policy(self) -> None:
        skill = read(".claude/skills/provider-routing/SKILL.md")
        for phrase in (
            "omit invocation-level `model`",
            "H** = Fable/low or Opus/high",
            "X** = Fable at medium\u2013xhigh or Opus/high",
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
            "[LEAF_DISPATCH]",
            "[LEAF_RESULT]",
        ):
            self.assertIn(phrase, skill)
        self.assertIn("${CODEX_HOME:-$HOME/.codex}/scripts/model-routing", skill)
        self.assertNotIn("--model gpt-5.6-sol", skill)


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
            "Load the `leaf-dispatch` skill before ANY dispatch",
        ):
            self.assertIn(phrase, agents)
        self.assertNotIn("Discovery → Plan → Approval", agents)

    def test_codex_dispatch_detail_lives_in_leaf_dispatch_skill(self) -> None:
        skill = " ".join(read(".codex/skills/leaf-dispatch/SKILL.md").split())
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
        self.assertIn("GPT-5.6 Sol/high", read(".codex/AGENTS.contract.md"))
        self.assertIn("The user owns the Codex GPT model", read(".codex/AGENTS.contract.md"))

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
        # Claude role -> codex agent file (Explore is lowercase on the codex side).
        counterparts = {
            "Explore": "explore",
            "plan-verifier": "plan-verifier",
            "security-reviewer": "security-reviewer",
            "mech-executor": "mech-executor",
            "executor": "executor",
            "verifier": "verifier",
            "security-executor": "security-executor",
        }
        config = tomllib.loads(read(".codex/config.merge.toml"))
        read_only = {"explore", "plan-verifier", "security-reviewer", "verifier"}
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
        allowed = routing["quality_floor"]["allowed"]
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
                    allowed[role_tiers[role]],
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
        script = ROOT / ".codex/scripts/model-routing"
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
        self.assertIn((".codex/model-routing.toml", ".codex/model-routing.toml"), managed)
        self.assertIn((".codex/scripts", ".codex/scripts"), managed)
        agents = read(".codex/AGENTS.contract.md")
        self.assertIn("${CODEX_HOME:-$HOME/.codex}/scripts/model-routing", agents)
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
            "never replace `config.toml`",
            "Credentials and login",
            "Authentication only",
            "Keep approval enabled",
        ):
            self.assertIn(phrase, deploy)
        self.assertNotIn("/Users/", deploy)
        self.assertIn("not automatic deployment", analysis)
        self.assertIn("Git is the cross-machine source of truth", analysis)


class DocumentationBudgetTests(unittest.TestCase):
    def test_docs_stay_distilled(self) -> None:
        # Word budgets, not line budgets — a line count is gameable by long
        # lines; words track resident attention cost. Raising a budget is a
        # deliberate decision, not a mechanical bump.
        # Units are word_count() words: one per CJK character, one per other
        # non-space run — zh-TW prose pays the same attention tax as English.
        budgets = {
            ".claude/CLAUDE.contract.md": 520,
            # Root README owns the complete architecture overview and diagrams;
            # operational/research detail remains linked in docs/.
            "README.md": 2250,
            "docs/README.md": 640,
            "docs/harness-engineering.md": 2350,
            ".claude/plans/orchestration-plan.md": 1300,
            ".codex/AGENTS.contract.md": 590,
            ".codex/ANALYSIS.md": 500,
            ".codex/DEPLOY.md": 550,
            ".claude/skills/baton-dispatch/SKILL.md": 890,
            ".claude/skills/provider-routing/SKILL.md": 1480,
            ".codex/skills/leaf-dispatch/SKILL.md": 720,
        }
        for path, limit in budgets.items():
            self.assertLessEqual(word_count(read(path)), limit, path)

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
            "README.md", "docs/README.md", ".claude/README.md",
            ".codex/README.md", ".agents/README.md",
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
        self.assertIn("Baton `0ab4d2e`", plan)
        self.assertIn("MIT", readme)
        self.assertIn("Yuhuan", read("LICENSE"))
        self.assertIn("P(win)>=0.90", plan)
        self.assertNotIn("AR lead >=10pt", plan)

    def test_harness_engineering_keeps_role_boundaries_local(self) -> None:
        doc = read("docs/harness-engineering.md")
        research = read("docs/harness-engineering-research.md")
        self.assertIn("main-only 段必須短", doc)
        self.assertIn("角色檔要自足", doc)
        self.assertIn("每個可接受成果的預期總成本", doc)
        self.assertIn("完整主張可反駁的最小整合邊界", doc)
        self.assertIn("stable brief", doc)
        self.assertIn("研究摘要不再複製容易過期的 route 表格", research)



if __name__ == '__main__':
    unittest.main()
