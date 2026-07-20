from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLES = (
    "Explore",
    "plan-verifier",
    "security-reviewer",
    "security-reviewer-xhigh",
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
    "security-executor-xhigh",
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def frontmatter(path: str) -> str:
    return read(path).split("---", 2)[1]


class OrchestrationContractTests(unittest.TestCase):
    def test_every_named_role_owns_its_model(self) -> None:
        policy = read("CLAUDE.md")
        self.assertIn("omit invocation-level `model`", policy)
        self.assertEqual(
            {path.stem for path in (ROOT / "agents").glob("*.md")},
            set(ROLES),
        )

        for role in ROLES:
            metadata = frontmatter(f"agents/{role}.md")
            self.assertIn(f"name: {role}\n", metadata)
            self.assertRegex(metadata, r"(?m)^model:\s*\S+\s*$")
            body = read(f"agents/{role}.md")
            self.assertNotIn("CLAUDE.md", body)
            self.assertNotIn("baton-dispatch", body)
            self.assertNotIn("orchestration skill", body)

        for role in (
            "Explore",
            "plan-verifier",
            "security-reviewer",
            "security-reviewer-xhigh",
        ):
            metadata = frontmatter(f"agents/{role}.md")
            self.assertRegex(metadata, r"(?m)^tools:\s*.+$")
            self.assertNotIn("Agent", metadata)
            self.assertNotIn("Workflow", metadata)

        for role in (
            "mech-executor",
            "executor",
            "verifier",
            "security-executor",
            "security-executor-xhigh",
        ):
            metadata = frontmatter(f"agents/{role}.md")
            self.assertRegex(metadata, r"(?m)^disallowedTools:.*\bAgent\b.*\bWorkflow\b")

    def test_baton_dispatch_brake_replaces_fixed_phase_pipeline(self) -> None:
        policy = read("CLAUDE.md")
        skill = read("skills/baton-dispatch/SKILL.md")
        for question in (
            "observable outcome",
            "delegation beats direct work",
            "one owner per writable artifact",
            "integration and final-verification owner",
        ):
            self.assertIn(question, policy)
        self.assertIn("Direct execution is the default", policy)
        self.assertIn("not request bullets", policy)
        self.assertIn("one unknown bug's diagnosis", policy)
        self.assertIn("one bounded `Explore` run", policy)
        self.assertIn("Converge shared schemas", policy)
        self.assertIn("Do not use for small edits", frontmatter("skills/baton-dispatch/SKILL.md"))
        self.assertIn("Known one-file fix", read("skills/baton-dispatch/references/briefs-and-stops.md"))
        self.assertIn("cablate/baton v0.1.1", skill)
        self.assertIn("scope fix `0ab4d2e`", skill)
        self.assertNotIn("why delegation beats direct work", skill)
        self.assertIn("explicit opt-in", policy)
        self.assertIn("user opt-in", skill)
        self.assertNotIn("Discovery → Plan → Approval", policy + skill)

    def test_result_collection_and_agent_continuation_are_distinct(self) -> None:
        policy = read("CLAUDE.md")
        self.assertIn("Collect each finished agent's final response", policy)
        self.assertIn("genuinely new or redirected work", policy)
        self.assertIn("never relaunch to restate a result", policy)

        agent = read("agents/Explore.md")
        self.assertIn("final response is the complete deliverable", agent)
        self.assertIn("genuinely new or redirected work", agent)
        self.assertIn("never repeat a completed search", agent)

    def test_delegation_preserves_the_approved_scope(self) -> None:
        policy = read("CLAUDE.md")
        skill = read("skills/baton-dispatch/SKILL.md")
        brief = read("skills/baton-dispatch/references/briefs-and-stops.md")
        codex = read("distilled/codex-chatgpt/codex/AGENTS.md")

        for text in (policy, skill, codex):
            self.assertIn("hard boundary", text)
            self.assertIn("adjacent", text)
        self.assertIn("excluded adjacent capabilities", brief)
        self.assertIn("approved boundary crossed", brief)

    def test_main_profile_is_user_owned_and_named_roles_are_pinned(self) -> None:
        settings = json.loads(read("settings.json"))
        for key in ("model", "effortLevel", "fallbackModel"):
            self.assertNotIn(key, settings)
        self.assertNotIn("claude-mem@thedotmack", settings["enabledPlugins"])
        self.assertNotIn("thedotmack", settings["extraKnownMarketplaces"])
        self.assertIn("H = Fable/low or Opus/high", read("CLAUDE.md"))
        self.assertIn("X = Fable/medium or Opus/xhigh", read("CLAUDE.md"))
        for role in ("plan-verifier", "verifier"):
            metadata = frontmatter(f"agents/{role}.md")
            self.assertIn("model: opus", metadata)
            self.assertIn("effort: high", metadata)
        self.assertIn("model: opus", frontmatter("agents/verifier.md"))
        self.assertIn("model: opus", frontmatter("agents/executor.md"))

    def test_global_policy_avoids_forced_questions_and_protects_user_state(self) -> None:
        policy = read("CLAUDE.md")
        self.assertIn("Infer low-risk ambiguity", policy)
        self.assertIn("different answers materially change the result", policy)
        self.assertIn("preserve dirty worktrees", policy)
        self.assertIn("destructive actions", policy)
        self.assertIn("require explicit authority", policy)
        self.assertNotIn("what does done look like", policy)
        self.assertNotIn("Think in English", policy)
        self.assertNotIn("End substantial tasks with `NOTED:`", policy)

    def test_output_contract_is_outcome_first_without_rigid_templates(self) -> None:
        claude = read("CLAUDE.md")
        codex = read("distilled/codex-chatgpt/codex/AGENTS.md")
        chatgpt = read("distilled/codex-chatgpt/chatgpt/custom-instructions.md")

        self.assertIn("Lead with the outcome", claude)
        self.assertIn("Final reports contain only", claude)
        self.assertIn("Lead with the outcome", codex)
        self.assertIn("Report only outcome", codex)
        self.assertNotIn("NOTED:", codex)
        self.assertIn("Lead with the direct answer", chatgpt)
        self.assertNotIn("Always use exactly these headings", claude + codex + chatgpt)

    def test_plan_and_outcome_verifiers_are_capability_separated(self) -> None:
        policy = read("CLAUDE.md")
        plan = read("agents/plan-verifier.md")
        outcome = read("agents/verifier.md")

        self.assertIn("tools: Read, Glob, Grep", plan)
        self.assertNotIn("Bash", frontmatter("agents/plan-verifier.md"))
        self.assertIn("READY", plan)
        self.assertIn("REVISE", plan)
        self.assertNotIn("CONFIRMED", plan)
        self.assertIn("CONFIRMED", outcome)
        self.assertIn("REFUTED", outcome)
        self.assertNotIn("READY", outcome)
        self.assertIn("`plan-verifier` returns READY/REVISE", policy)
        self.assertIn("`verifier` returns CONFIRMED/REFUTED", policy)
        self.assertIn("isolated worktree", outcome)
        self.assertIn("git status --short", outcome)
        self.assertIn("must be identical", outcome)

    def test_opus_verifier_is_main_session_risk_triggered(self) -> None:
        policy = read("CLAUDE.md")
        self.assertIn("## Main session only — orchestration", policy)
        self.assertIn("MAIN-SESSION-ONLY: START", policy)
        self.assertIn("MAIN-SESSION-ONLY: END", policy)
        self.assertIn("### Verification routing", policy)
        for trigger in (
            "security/trust boundary",
            "judgment-heavy integration",
            "adversarial state or boundary behavior",
            "evidence conflicts",
        ):
            self.assertIn(trigger, policy)
        self.assertIn("Do not dispatch it for docs-only", policy)

    def test_codex_sol_uses_real_namespaced_role_and_honest_boundary(self) -> None:
        policy = read("CLAUDE.md")
        self.assertIn("`codex:codex-rescue`", policy)
        self.assertIn("--model gpt-5.6-sol", policy)
        self.assertIn("--effort high|xhigh", policy)
        self.assertIn("write-capable by default", policy)
        self.assertIn("explicitly prohibit writes", policy)
        self.assertNotIn("Sol via `codex-rescue` is read-only", policy)

    def test_cross_provider_fallback_is_single_hop_and_user_gated(self) -> None:
        policy = read("CLAUDE.md")

        self.assertIn("one cross-provider hop measured from the task's origin", policy)
        self.assertIn("A fallback provider cannot route back", policy)
        self.assertIn("one bounded retry", policy)
        for option in (
            "Dispatch GPT + Claude",
            "Dispatch GPT",
            "Dispatch Claude",
        ):
            self.assertIn(option, policy)
        self.assertIn("never two writers", policy)

    def test_distilled_bundle_avoids_claude_routing_policy(self) -> None:
        files = sorted((ROOT / "distilled").rglob("*"))
        body = "\n".join(
            path.read_text(encoding="utf-8") for path in files if path.is_file()
        )
        lowered = body.lower()

        for forbidden in (
            "claude",
            "fable",
            "opus",
            "dispatch gpt +",
            "dispatch claude",
            "manual handoff",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("GPT-5.6 Sol/high", body)
        self.assertIn("The user owns the Codex GPT model and reasoning effort", body)

    def test_security_approval_boundary_is_capability_enforced(self) -> None:
        policy = read("CLAUDE.md")
        for suffix, effort in (("", "high"), ("-xhigh", "xhigh")):
            reviewer_path = f"agents/security-reviewer{suffix}.md"
            executor_path = f"agents/security-executor{suffix}.md"
            reviewer = read(reviewer_path)
            executor = read(executor_path)
            for path in (reviewer_path, executor_path):
                metadata = frontmatter(path)
                self.assertIn("model: opus", metadata)
                self.assertIn(f"effort: {effort}", metadata)
            self.assertIn("tools: Read, Glob, Grep, WebSearch, WebFetch", reviewer)
            self.assertNotIn("Bash", frontmatter(reviewer_path))
            self.assertIn("approved scope, constraints, abuse case, and done-criteria", executor)
            self.assertIn(
                f"pre-approval analysis belongs to `security-reviewer{suffix}`",
                executor,
            )
            if suffix:
                self.assertIn("GPT X fails", frontmatter(reviewer_path))
                self.assertIn("GPT X fails", frontmatter(executor_path))
        self.assertIn("Security remains GPT-primary", policy)
        self.assertIn("never Fable", policy)
        self.assertIn("GPT writes", policy)
        self.assertIn("Claude main session verifies", policy)

    def test_bash_capable_leaf_roles_never_detach(self) -> None:
        for role in (
            "mech-executor",
            "executor",
            "verifier",
            "security-executor",
            "security-executor-xhigh",
        ):
            agent = read(f"agents/{role}.md")
            self.assertIn("commands in the foreground", agent)
            self.assertIn("at most 10 minutes", agent)
            self.assertIn("absolute working directory", agent)
            self.assertIn("required environment", agent)
            self.assertIn("inputs", agent)

        policy = read("CLAUDE.md")
        self.assertIn("Long-running processes remain in the main session", policy)
        self.assertIn("bounded foreground commands", policy)

    def test_settings_have_one_rtk_hook_and_runtime_guard(self) -> None:
        settings = json.loads(read("settings.json"))
        pre_tool_commands = [
            hook["command"]
            for group in settings["hooks"]["PreToolUse"]
            for hook in group["hooks"]
        ]
        self.assertEqual(sum("rtk hook claude" in command for command in pre_tool_commands), 1)

        session_commands = [
            hook["command"]
            for group in settings["hooks"]["SessionStart"]
            for hook in group["hooks"]
        ]
        self.assertEqual(sum("runtime-guard.py" in command for command in session_commands), 1)
        self.assertFalse(
            any(
                "headroom init hook ensure" in command
                for command in (*pre_tool_commands, *session_commands)
            )
        )

        allowed = set(settings["permissions"]["allow"])
        for broad_rule in (
            "Bash(git branch:*)",
            "Bash(cat:*)",
            "Bash(echo:*)",
            "Bash(npx tsc:*)",
            "Bash(npx eslint:*)",
        ):
            self.assertNotIn(broad_rule, allowed)
        self.assertNotIn("skipWorkflowUsageWarning", settings)
        self.assertNotIn(
            "claude-for-financial-services",
            settings["extraKnownMarketplaces"],
        )

    def test_headroom_wrap_mode_is_portable_and_machine_local(self) -> None:
        self.assertFalse((ROOT / ".claude.json").exists())
        mcp_text = read("examples/headroom-mcp.merge.json")
        settings_text = read("settings.json")
        mcp = json.loads(mcp_text)["mcpServers"]
        settings = json.loads(settings_text)
        policy = read("CLAUDE.md")
        readme = read("README.md")

        self.assertEqual(mcp["headroom"], {"command": "headroom", "args": ["mcp", "serve"]})
        self.assertNotIn("/Users/", mcp_text)
        self.assertNotIn("/Users/", settings_text)
        self.assertNotIn("ANTHROPIC_BASE_URL", settings.get("env", {}))
        self.assertIn("proxy routing is absent", policy)
        self.assertIn("headroom wrap claude --tool-search true", readme)
        self.assertIn("標準 context 明確不足", readme)
        runtime = read("docs/headroom-runtime.md")
        self.assertIn("`tokensave`", runtime)
        self.assertIn("machine-local", runtime)
        # v0.32: wrap is the recommended default; persistent install is documented as an
        # optional always-on alternative, and neither mode commits a base URL to tracked settings.
        self.assertIn("headroom install", runtime)
        self.assertNotIn("淘汰", runtime)
        self.assertNotIn("deprecated", runtime.lower())

    def test_sol_is_not_a_fixed_second_verifier_pass(self) -> None:
        policy = read("CLAUDE.md")
        self.assertIn("Do not stack gates over the same failure surface", policy)
        self.assertIn("Dual-provider review", policy)
        self.assertIn("low-risk direct work", policy)
        self.assertNotIn("with the first `verifier` pass", policy)

    def test_distilled_bundle_tracks_current_capability_contracts(self) -> None:
        base = "distilled/codex-chatgpt/"
        analysis = read(base + "ANALYSIS.md")
        deploy = read(base + "DEPLOY.md")
        agents = read(base + "codex/AGENTS.md")
        verifier_text = read(base + "codex/agents/verifier.toml")
        verifier = tomllib.loads(verifier_text)
        config = tomllib.loads(read(base + "codex/config.merge.toml"))
        skill = read(base + "codex/skills/headroom-protocol/SKILL.md")
        custom = read(base + "chatgpt/custom-instructions.md")

        self.assertIn("not automatic deployment", analysis)
        self.assertIn("Git is the cross-machine source of truth", analysis)
        self.assertIn("Codex／ChatGPT 跨機器部署流程", read("README.md"))
        self.assertFalse((ROOT / base / "codex/hooks.optimized.json").exists())
        self.assertIn("Main task only — orchestration", agents)
        self.assertIn("Direct execution is the default", agents)
        self.assertIn("not request bullets", agents)
        self.assertIn("one unknown bug's diagnosis", agents)
        self.assertIn("preserve partial evidence", agents)
        self.assertIn("Centralize repository-wide, live, or expensive gates", agents)
        self.assertIn("hard boundary", agents)
        self.assertIn("Collect the finished subagent response", agents)
        self.assertIn("### Independent verifier", agents)
        self.assertNotIn("Discovery → Plan → Approval", agents)
        self.assertNotIn("otherwise non-trivial", verifier["description"])
        self.assertEqual(verifier["sandbox_mode"], "read-only")
        self.assertIn("routine low-risk work", verifier["description"])
        self.assertEqual(config["agents"]["max_depth"], 1)
        self.assertEqual(
            config["agents"]["verifier"]["config_file"],
            "./agents/verifier.toml",
        )
        self.assertIn("high-risk", config["agents"]["verifier"]["description"])
        self.assertIn("proxy routing is absent", skill)
        self.assertIn("Do not use for ordinary CLI work", frontmatter(base + "codex/skills/headroom-protocol/SKILL.md"))

        runtime_artifacts = "\n".join((agents, verifier_text, skill, custom)).lower()
        self.assertNotIn("claude-mem", runtime_artifacts)
        self.assertNotIn("headroom init hook ensure", runtime_artifacts)

        self.assertIn("## One-shot Codex command", deploy)
        self.assertIn("Codex deployment contract", deploy)
        self.assertIn("never replace `config.toml`", deploy)
        self.assertIn("Do not add or change Headroom", deploy)
        self.assertIn("only with explicit user authorization", deploy)
        self.assertIn("ChatGPT Personalization", deploy)
        self.assertIn("Credentials and login", deploy)
        self.assertIn("Authentication only", deploy)
        self.assertNotIn("/Users/", deploy)
        self.assertIn("Keep approval enabled", deploy)

    def test_documentation_is_distilled_and_role_boundaries_are_local(self) -> None:
        budgets = {
            "CLAUDE.md": 80,
            "README.md": 70,
            "docs/harness-engineering.md": 130,
            "plans/orchestration-plan.md": 80,
            "distilled/codex-chatgpt/ANALYSIS.md": 70,
            "distilled/codex-chatgpt/DEPLOY.md": 60,
            "distilled/codex-chatgpt/codex/AGENTS.md": 60,
        }
        for path, limit in budgets.items():
            self.assertLessEqual(len(read(path).splitlines()), limit, path)
        for role in ROLES:
            body = read(f"agents/{role}.md")
            self.assertLessEqual(len(body.splitlines()), 30, role)
            self.assertNotIn("CLAUDE.md", body)
            self.assertNotIn("baton-dispatch", body)
            self.assertNotIn("Before delegating", body)
            self.assertNotIn("provider choice", body)
            self.assertNotIn("Dispatch GPT + Claude", body)
        self.assertIn("do not brief them to read this section", read("CLAUDE.md"))
        self.assertIn("Subagents use their own role contract", read("distilled/codex-chatgpt/codex/AGENTS.md"))
        self.assertIn("main-only 段必須短", read("docs/harness-engineering.md"))
        self.assertIn("角色檔要自足", read("docs/harness-engineering.md"))

    def test_statusline_uses_payload_workspace_and_one_jq(self) -> None:
        script = read("sh/statusline.sh")
        branch = subprocess.run(
            ["git", "-C", str(ROOT), "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        payload = {
            "model": {"display_name": "Test"},
            "workspace": {"current_dir": str(ROOT)},
            "cost": {},
            "context_window": {},
        }
        with tempfile.TemporaryDirectory() as other_cwd:
            result = subprocess.run(
                ["bash", str(ROOT / "sh" / "statusline.sh")],
                cwd=other_cwd,
                input=json.dumps(payload),
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(script.count("| jq "), 1)
        self.assertIn("git -C \"$DIR\"", script)
        self.assertIn(ROOT.name, result.stdout)
        if branch:
            self.assertIn(f"({branch})", result.stdout)

    def test_weekly_integrity_stamps_only_after_completed_checks(self) -> None:
        hook = ROOT / "hooks" / "weekly-integrity.py"
        with tempfile.TemporaryDirectory() as temp_home:
            claude_dir = Path(temp_home) / ".claude"
            scripts_dir = claude_dir / "scripts"
            scripts_dir.mkdir(parents=True)
            report = scripts_dir / "delegation-report"
            report.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            report.chmod(0o755)
            env = {**os.environ, "HOME": temp_home}

            failed = subprocess.run(
                [sys.executable, str(hook)],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            stamp = claude_dir / "telemetry" / ".integrity-last-run"
            self.assertIn("contract-repo check failed", failed.stdout)
            self.assertFalse(stamp.exists())

            subprocess.run(
                ["git", "init", str(claude_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
            completed = subprocess.run(
                [sys.executable, str(hook)],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertNotIn("check failed", completed.stdout)
            self.assertTrue(stamp.exists())

    def test_runtime_guard_rejects_old_or_unknown_versions(self) -> None:
        guard = ROOT / "hooks" / "runtime-guard.py"
        old = subprocess.run(
            [sys.executable, str(guard), "2.1.197 (Claude Code)"],
            check=True,
            capture_output=True,
            text=True,
        )
        current = subprocess.run(
            [sys.executable, str(guard), "2.1.207 (Claude Code)"],
            check=True,
            capture_output=True,
            text=True,
        )
        unknown = subprocess.run(
            [sys.executable, str(guard), "development build"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("do not dispatch", old.stdout)
        self.assertIn("security-reviewer[-xhigh]", old.stdout)
        self.assertEqual(current.stdout, "")
        self.assertIn("version unknown", unknown.stdout)

    def test_usage_report_separates_sources_and_finds_rolling_peak(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            main = root / "project" / "main.jsonl"
            subagent = root / "project" / "session" / "subagents" / "agent.jsonl"
            observer = root / "claude-mem-observer-sessions" / "observer.jsonl"
            for path in (main, subagent, observer):
                path.parent.mkdir(parents=True, exist_ok=True)

            def record(timestamp: str, model: str, tokens: int) -> str:
                return json.dumps(
                    {
                        "type": "assistant",
                        "timestamp": timestamp,
                        "message": {
                            "model": model,
                            "usage": {
                                "input_tokens": tokens,
                                "output_tokens": 1,
                                "cache_creation_input_tokens": 2,
                                "cache_read_input_tokens": 3,
                            },
                        },
                    }
                )

            main.write_text(
                record("2026-07-15T00:00:00Z", "claude-sonnet-5", 10)
                + "\n"
                + record("2026-07-15T04:30:00Z", "claude-sonnet-5", 20)
                + "\n",
                encoding="utf-8",
            )
            subagent.write_text(
                record("2026-07-15T02:00:00Z", "claude-opus-4-8", 30) + "\n",
                encoding="utf-8",
            )
            observer.write_text(
                record("2026-07-15T08:00:00Z", "claude-sonnet-4-5", 40) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "usage-report"),
                    "--root",
                    str(root),
                    "--days",
                    "2",
                    "--now",
                    "2026-07-16T00:00:00Z",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(result.stdout)

        self.assertEqual(
            report["by_source_model"]["main"]["claude-sonnet-5"]["turns"], 2
        )
        self.assertEqual(
            report["by_source_model"]["subagent"]["claude-opus-4-8"]["turns"], 1
        )
        self.assertEqual(
            report["by_source_model"]["observer"]["claude-sonnet-4-5"]["turns"], 1
        )
        self.assertEqual(report["peak_rolling_window"]["turns"], 3)

    def test_usage_report_by_session_ranks_sessions_by_cache_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            heavy = root / "project" / "heavy.jsonl"
            light = root / "project" / "light.jsonl"
            for path in (heavy, light):
                path.parent.mkdir(parents=True, exist_ok=True)

            def record(timestamp: str, cache_read: int) -> str:
                return json.dumps(
                    {
                        "type": "assistant",
                        "timestamp": timestamp,
                        "message": {
                            "model": "claude-opus-4-8",
                            "usage": {
                                "input_tokens": 1,
                                "output_tokens": 1,
                                "cache_creation_input_tokens": 1,
                                "cache_read_input_tokens": cache_read,
                            },
                        },
                    }
                )

            heavy.write_text(
                record("2026-07-15T00:00:00Z", 500)
                + "\n"
                + record("2026-07-15T01:00:00Z", 500)
                + "\n",
                encoding="utf-8",
            )
            light.write_text(record("2026-07-15T00:00:00Z", 10) + "\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "usage-report"),
                    "--root",
                    str(root),
                    "--days",
                    "2",
                    "--now",
                    "2026-07-16T00:00:00Z",
                    "--by-session",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(result.stdout)

        rows = report["by_session"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["session"], "heavy")
        self.assertEqual(rows[0]["project"], "project")
        self.assertEqual(rows[0]["turns"], 2)
        self.assertEqual(rows[0]["cache_read_input_tokens"], 1000)
        self.assertEqual(rows[0]["models"], {"claude-opus-4-8": 2})
        self.assertLess(
            rows[1]["cache_read_input_tokens"], rows[0]["cache_read_input_tokens"]
        )

    def test_documented_baseline_matches_runtime_contract(self) -> None:
        settings = json.loads(read("settings.json"))
        readme = read("README.md")
        plan = read("plans/orchestration-plan.md")

        self.assertIn("pilotfish v1.2.1 `80b5d1f`", plan)
        self.assertIn("Baton `0ab4d2e`", plan)
        self.assertIn("2.1.207 以上版本", readme)
        self.assertIn("2.1.207", plan)
        self.assertNotIn("tracked default", readme)
        self.assertIn("主模型與 effort 由使用者選擇", readme)
        self.assertIn("九個自足的 Claude leaf roles", readme)
        self.assertIn("one cross-provider hop", read("CLAUDE.md"))
        self.assertIn("獨立 Codex", readme)
        self.assertIn("clone 至暫存路徑，再比對、備份與合併", readme)
        # claude-mem is fully retired from user-facing docs; plans keep it as history only.
        self.assertNotIn("claude-mem", readme)
        # The version gate is mechanism-owned (runtime-guard hook); CLAUDE.md must not restate it.
        self.assertNotIn("2.1.207", read("CLAUDE.md"))


if __name__ == "__main__":
    unittest.main()
