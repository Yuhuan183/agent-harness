from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Repo root: the tracked harness spans .claude/, .codex/, .agents/, and docs/.
ROOT = Path(__file__).resolve().parents[2]

ROLES = (
    "Explore",
    "plan-verifier",
    "security-reviewer",
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
)
CODEX_ROLES = tuple(role.lower() if role == "Explore" else role for role in ROLES)
READ_ONLY_ROLES = (
    "Explore",
    "plan-verifier",
    "security-reviewer",
)
BASH_ROLES = (
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
)
# Every role pins model and effort from the active deployment preset (user-directed
# 2026-07-22); no role follows the main-session effort.
PINNED_EFFORT_ROLES = ROLES
FOLLOW_EFFORT_ROLES = ()

# Interface tokens: single upgrade point — bump here and in the skill bodies together.
CODEX_BRIDGE = "codex:codex-rescue"
DISPATCH_OPTIONS = ("Dispatch GPT + Claude", "Dispatch GPT", "Dispatch Claude")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def deployment_manifest() -> list[tuple[str, str]]:
    pairs = []
    for raw in read("scripts/deployment-manifest.tsv").splitlines():
        if not raw or raw.startswith("#"):
            continue
        source, target = raw.split("\t")
        pairs.append((source, target))
    return pairs


def frontmatter(path: str) -> str:
    return read(path).split("---", 2)[1]


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
    )


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
        self.assertIn("Report every dispatch to the user", policy)
        self.assertIn("Quality-check every result", policy)
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
        self.assertIn("Do not use for small edits", frontmatter(".claude/skills/baton-dispatch/SKILL.md"))
        # Cost test: high-tier pinned delegation saves no compute; payoff must beat overhead.
        self.assertIn("## Cost test", skill)
        self.assertIn("delegation saves no compute", skill)
        self.assertIn("clearly exceeds dispatch overhead", read(".claude/CLAUDE.contract.md"))
        self.assertIn("clearly exceeds dispatch overhead", read(".codex/AGENTS.contract.md"))
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
            "never Fable",
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
        self.assertEqual(sum("runtime-guard.py" in c for c in start), 1)


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
        ):
            self.assertIn(phrase, agents)
        self.assertNotIn("Discovery → Plan → Approval", agents)

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
        self.assertIn("Report every dispatch to the user", agents)
        self.assertIn("quality-check it against the brief", agents)
        self.assertIn("Never brief a subagent to delegate further", agents)

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


class SharedSkillTests(unittest.TestCase):
    def _assert_symlinked_body(self, name: str) -> None:
        body = ROOT / ".agents/skills" / name
        self.assertTrue((body / "SKILL.md").is_file(), f"{name} body missing")
        for stub in (f".claude/skills/{name}", f".codex/skills/{name}"):
            link = ROOT / stub
            self.assertTrue(link.is_symlink(), f"{stub} is not a symlink")
            self.assertEqual(os.readlink(link), f"../../.agents/skills/{name}")
            self.assertTrue((link / "SKILL.md").is_file(), f"{stub} does not resolve")

    def test_headroom_protocol_is_shared_via_symlink(self) -> None:
        self._assert_symlinked_body("headroom-protocol")

    def test_speak_human_tw_is_shared_via_symlink(self) -> None:
        self._assert_symlinked_body("speak-human-tw")

    def test_speak_human_tw_layout_and_attribution(self) -> None:
        base = ".agents/skills/speak-human-tw"
        for ref in ("patterns", "taiwan-localization", "protected-list", "humanize"):
            self.assertTrue((ROOT / base / "references" / f"{ref}.md").is_file(), ref)
        self.assertTrue((ROOT / base / "agents/openai.yaml").is_file())
        meta = frontmatter(f"{base}/SKILL.md")
        self.assertIn("name: speak-human-tw", meta)
        self.assertIn("user-invocable: true", meta)
        self.assertIn("license: MIT", meta)
        skill = read(f"{base}/SKILL.md")
        for ref in ("patterns.md", "taiwan-localization.md", "protected-list.md", "humanize.md"):
            self.assertIn(ref, skill)
        # MIT derivative must carry the upstream notice.
        attribution = read(f"{base}/ATTRIBUTION.md")
        self.assertIn("MIT", attribution)
        self.assertIn("Raymond Hou", attribution)
        self.assertIn("Raymondhou0917/speak-human-tw", attribution)

    def test_shared_skill_names_are_listed(self) -> None:
        installed = read(".agents/skills/INSTALLED.txt").splitlines()
        self.assertIn("headroom-protocol", installed)
        self.assertIn("speak-human-tw", installed)
        self.assertIn("experience-ledger", installed)

    def test_experience_ledger_is_shared_and_wired(self) -> None:
        self._assert_symlinked_body("experience-ledger")
        base = ROOT / ".agents/skills/experience-ledger"
        for script in ("experience-log", "experience-report", "experience-revise"):
            path = base / "scripts" / script
            self.assertTrue(path.is_file(), script)
            self.assertTrue(os.access(path, os.X_OK), f"{script} not executable")
        self.assertTrue((base / "references/metrics.md").is_file())
        # provider-routing points dispatch experience at the ledger skill.
        routing = read(".claude/skills/provider-routing/SKILL.md")
        self.assertIn("experience-ledger", routing)
        self.assertIn("log every dispatch outcome after QC", routing)

    def test_experience_scripts_log_and_report(self) -> None:
        base = ROOT / ".agents/skills/experience-ledger/scripts"
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = os.path.join(temp_dir, "experience.jsonl")
            env = {**os.environ, "AGENT_EXPERIENCE_LEDGER": ledger}

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

    def test_experience_pending_pairs_by_session_and_consumes_one_dispatch(self) -> None:
        hook = ROOT / ".claude/hooks/experience-pending.py"
        log_script = ROOT / ".agents/skills/experience-ledger/scripts/experience-log"
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
        log_script = ROOT / ".agents/skills/experience-ledger/scripts/experience-log"
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
        log_script = ROOT / ".agents/skills/experience-ledger/scripts/experience-log"
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
                     "AGENT_EXPERIENCE_LEDGER": str(ledger)},
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("production records require a resolved route", result.stderr)
            self.assertEqual(pending.read_text(encoding="utf-8"), before)
            self.assertFalse(ledger.exists())

    def test_experience_report_never_mixes_total_and_output_only_cost(self) -> None:
        report_script = ROOT / ".agents/skills/experience-ledger/scripts/experience-report"
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
                        "model": ("claude-sonnet-5" if provider == "claude"
                                  else "gpt-5.6-sol"),
                        "effort": "high" if provider == "claude" else "medium",
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
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger)},
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
        report_script = ROOT / ".agents/skills/experience-ledger/scripts/experience-report"
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
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger)},
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
        report_script = ROOT / ".agents/skills/experience-ledger/scripts/experience-report"
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
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger)},
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

    def test_experience_report_renders_all_legacy_cohorts(self) -> None:
        report_script = ROOT / ".agents/skills/experience-ledger/scripts/experience-report"
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
                env={**os.environ, "AGENT_EXPERIENCE_LEDGER": str(ledger)},
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Explore", result.stdout)
        self.assertIn("mech-executor", result.stdout)
        self.assertIn("legacy-unknown", result.stdout)
        self.assertNotIn("TypeError", result.stderr)


class DocumentationBudgetTests(unittest.TestCase):
    def test_docs_stay_distilled(self) -> None:
        budgets = {
            ".claude/CLAUDE.contract.md": 40,
            "README.md": 70,
            "docs/harness-engineering.md": 130,
            ".claude/plans/orchestration-plan.md": 80,
            ".codex/AGENTS.contract.md": 60,
            ".codex/ANALYSIS.md": 70,
            ".codex/DEPLOY.md": 60,
            ".claude/skills/baton-dispatch/SKILL.md": 55,
            ".claude/skills/provider-routing/SKILL.md": 55,
        }
        for path, limit in budgets.items():
            self.assertLessEqual(len(read(path).splitlines()), limit, path)

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
        self.assertIn("main-only 段必須短", doc)
        self.assertIn("角色檔要自足", doc)
        self.assertIn("每個可接受成果的預期總成本", doc)


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
                ["bash", str(ROOT / ".claude/sh/statusline.sh")],
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
        guard = ROOT / ".claude/hooks/runtime-guard.py"
        old = subprocess.run([sys.executable, str(guard), "2.1.197 (Claude Code)"],
                             check=True, capture_output=True, text=True)
        current = subprocess.run([sys.executable, str(guard), "2.1.207 (Claude Code)"],
                                 check=True, capture_output=True, text=True)
        unknown = subprocess.run([sys.executable, str(guard), "development build"],
                                 check=True, capture_output=True, text=True)
        self.assertIn("do not dispatch", old.stdout)
        self.assertIn("security-reviewer", old.stdout)
        self.assertEqual(current.stdout, "")
        self.assertIn("version unknown", unknown.stdout)

    def test_weekly_integrity_stamps_only_after_completed_checks(self) -> None:
        hook = ROOT / ".claude/hooks/weekly-integrity.py"
        with tempfile.TemporaryDirectory() as temp_home:
            claude_dir = Path(temp_home) / ".claude"
            scripts_dir = claude_dir / "scripts"
            scripts_dir.mkdir(parents=True)
            report = scripts_dir / "delegation-report"
            report.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            report.chmod(0o755)
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
            (repo / ".claude").mkdir(parents=True)
            (repo / ".claude" / "CLAUDE.contract.md").write_text("contract\n",
                                                                 encoding="utf-8")
            (repo / "scripts").mkdir()
            (repo / "scripts/deployment-manifest.tsv").write_text(
                ".claude/CLAUDE.contract.md\t.claude/CLAUDE.md\n",
                encoding="utf-8",
            )
            env["AGENT_HARNESS_REPO"] = str(repo)
            drifted = subprocess.run([sys.executable, str(hook)], env=env,
                                     check=True, capture_output=True, text=True)
            self.assertIn("deployment drift", drifted.stdout)
            self.assertIn("dispatch-experience gap", drifted.stdout)
            self.assertNotIn("check failed", drifted.stdout)
            self.assertTrue(stamp.exists())

            # No git and no harness checkout either: skip gracefully.
            stamp.unlink()
            env["AGENT_HARNESS_REPO"] = str(Path(temp_home) / "missing")
            skipped = subprocess.run([sys.executable, str(hook)], env=env,
                                     check=True, capture_output=True, text=True)
            self.assertNotIn("check failed", skipped.stdout)
            self.assertTrue(stamp.exists())

            # ~/.claude as a git checkout keeps the original git-status path.
            stamp.unlink()
            subprocess.run(["git", "init", str(claude_dir)], check=True,
                           capture_output=True, text=True)
            completed = subprocess.run([sys.executable, str(hook)], env=env,
                                       check=True, capture_output=True, text=True)
            self.assertNotIn("check failed", completed.stdout)
            self.assertTrue(stamp.exists())

    def test_sync_and_weekly_integrity_share_one_deployment_manifest(self) -> None:
        hook = read(".claude/hooks/weekly-integrity.py")
        sync = read("scripts/sync.sh")
        pairs = deployment_manifest()
        sources = [source for source, _ in pairs]
        targets = [target for _, target in pairs]
        self.assertEqual(len(sources), len(set(sources)))
        self.assertEqual(len(targets), len(set(targets)))
        self.assertIn("deployment-manifest.tsv", hook)
        self.assertIn("deployment-manifest.tsv", sync)
        self.assertNotIn("cross_platform =", hook)
        self.assertIn((".claude/CLAUDE.contract.md", ".claude/CLAUDE.md"), pairs)
        self.assertIn((".codex/AGENTS.contract.md", ".codex/AGENTS.md"), pairs)
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
        self.assertIn("dry-run 完成", result.stdout)

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
            for source_rel, target_rel in deployment_manifest():
                source = ROOT / source_rel
                target = Path(temp_home) / target_rel
                if source.is_dir():
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
            self.assertIn("已停止 apply", result.stdout)
            self.assertEqual(settings_path.read_text(encoding="utf-8"), before)
            self.assertFalse((Path(temp_home) / ".codex").exists())

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
                [sys.executable, str(ROOT / ".claude/scripts/usage-report"),
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
                [sys.executable, str(ROOT / ".claude/scripts/usage-report"),
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


if __name__ == "__main__":
    unittest.main()
