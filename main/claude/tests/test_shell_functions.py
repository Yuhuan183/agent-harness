"""Behavioral tests for the shared agent-launch zsh functions."""
from support import *  # noqa: F401,F403


INSTALLER = ROOT / "scripts/install-zsh-functions.sh"


class AgentLaunchFunctionTests(unittest.TestCase):
    def function_block(self) -> str:
        return subprocess.run(
            [str(INSTALLER), "--print-block"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def run_function(
        self, invocation: str, *, agy_supported: bool = True,
        model_env: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            block = temp / "functions.zsh"
            block.write_text(self.function_block(), encoding="utf-8")
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            call_log = temp / "calls.tsv"

            headroom = bin_dir / "headroom"
            headroom.write_text(
                """#!/bin/sh
if [ "$1" = "wrap" ] && [ "$3" = "--help" ]; then
  if [ "$2" = "agy" ] && [ "${HEADROOM_AGY_SUPPORTED:-0}" != "1" ]; then
    exit 2
  fi
  exit 0
fi
{
  printf 'headroom'
  for arg in "$@"; do printf '\\t%s' "$arg"; done
  printf '\\n'
} >> "$CALL_LOG"
printf '%s\\n' "${HEADROOM_1M_MODEL-<unset>}" >> "$MODEL_LOG"
""",
                encoding="utf-8",
            )
            headroom.chmod(0o755)

            for agent_name in ("claude", "codex", "agy"):
                agent = bin_dir / agent_name
                agent.write_text(
                    f"""#!/bin/sh
{{
  printf '{agent_name}'
  for arg in "$@"; do printf '\\t%s' "$arg"; done
  printf '\\n'
}} >> "$CALL_LOG"
""",
                    encoding="utf-8",
                )
                agent.chmod(0o755)

            model_log = temp / "models.txt"
            env = os.environ.copy()
            # The caller's shell may carry either knob; each case states its own.
            env.pop("HEADROOM_1M_MODEL", None)
            env.pop("ANTHROPIC_MODEL", None)
            env.update(model_env or {})
            env.update(
                {
                    "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
                    "CALL_LOG": str(call_log),
                    "MODEL_LOG": str(model_log),
                    "FUNCTION_BLOCK": str(block),
                    "HEADROOM_AGY_SUPPORTED": "1" if agy_supported else "0",
                }
            )
            result = subprocess.run(
                ["zsh", "-dfc", f'source "$FUNCTION_BLOCK"; {invocation}'],
                capture_output=True,
                text=True,
                env=env,
            )
            calls = call_log.read_text(encoding="utf-8").splitlines() if call_log.exists() else []
            self.models_seen = (model_log.read_text(encoding="utf-8").splitlines()
                                if model_log.exists() else [])
            return result, calls

    def test_print_block_is_the_single_complete_function_source(self) -> None:
        block = self.function_block()
        for function_name in (
            "_agent_harness_headroom_wrap",
            "claude-auto",
            "codex-auto",
            "agy-auto",
            "hclaude",
            "hcodex",
            "hagy",
            "hclaude-auto",
            "hcodex-auto",
            "hagy-auto",
        ):
            self.assertIn(f"{function_name}() {{", block)
        self.assertEqual(block.count("# >>> agent-harness auto-mode functions >>>"), 1)
        self.assertEqual(block.count("# <<< agent-harness auto-mode functions <<<"), 1)
        self.assertNotIn("--no-context-tool", block)
        self.assertNotIn("--context-tool", block)

    def test_platform_commands_preserve_arguments_and_safety_modes(self) -> None:
        cases = {
            "claude-auto 'two words'": [
                "claude",
                "--permission-mode",
                "auto",
                "two words",
            ],
            "codex-auto 'two words'": [
                "codex",
                "-a",
                "on-request",
                "-s",
                "workspace-write",
                "two words",
            ],
            "agy-auto --effort high 'two words'": [
                "agy",
                "--mode",
                "accept-edits",
                "--effort",
                "high",
                "two words",
            ],
            # `--1m` before the separator, or Headroom never sees it and the
            # session silently caps at 200k.
            "hclaude 'two words'": [
                "headroom",
                "wrap",
                "claude",
                "--1m",
                "--",
                "two words",
            ],
            "hcodex 'two words'": [
                "headroom",
                "wrap",
                "codex",
                "--",
                "two words",
            ],
            "hagy 'two words'": [
                "headroom",
                "wrap",
                "agy",
                "--",
                "two words",
            ],
            "hclaude-auto 'two words'": [
                "headroom",
                "wrap",
                "claude",
                "--1m",
                "--",
                "--permission-mode",
                "auto",
                "two words",
            ],
            "hcodex-auto 'two words'": [
                "headroom",
                "wrap",
                "codex",
                "--",
                "-a",
                "on-request",
                "-s",
                "workspace-write",
                "two words",
            ],
            "hagy-auto 'two words'": [
                "headroom",
                "wrap",
                "agy",
                "--",
                "--mode",
                "accept-edits",
                "two words",
            ],
        }
        for invocation, expected in cases.items():
            with self.subTest(invocation=invocation):
                result, calls = self.run_function(invocation)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0].split("\t"), expected)

    def test_hclaude_names_a_family_not_a_generation(self) -> None:
        # `--1m` makes Headroom set ANTHROPIC_MODEL, falling back to
        # HEADROOM_1M_MODEL and then to a built-in generation id
        # (`claude-opus-5`, still so in Headroom 0.39.1). That pinned every
        # hclaude session to one generation. The family alias lets the CLI pick
        # the current one: `opus[1m]` ran as claude-opus-5-5[1m] with a 1M
        # window behind the proxy on 2026-09-30.
        for invocation in ("hclaude 'two words'", "hclaude-auto 'two words'"):
            with self.subTest(invocation=invocation):
                result, _ = self.run_function(invocation)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.models_seen, ["opus"])
        # A preference the user set is theirs. An ANTHROPIC_MODEL they set
        # outranks both inside Headroom itself (`_resolve_1m_model`), which a
        # stub cannot show, so it is not asserted here.
        result, _ = self.run_function("hclaude", model_env={"HEADROOM_1M_MODEL": "sonnet"})
        self.assertEqual(self.models_seen, ["sonnet"])
        # hcodex has no 1M flag and gets nothing.
        result, _ = self.run_function("hcodex")
        self.assertEqual(self.models_seen, ["<unset>"])

    def test_hagy_fails_closed_when_headroom_has_no_agy_adapter(self) -> None:
        result, calls = self.run_function("hagy --print hello", agy_supported=False)
        self.assertEqual(result.returncode, 127)
        self.assertEqual(calls, [])
        self.assertIn("does not support 'wrap agy'", result.stderr)
        self.assertIn("refusing to launch the agent directly", result.stderr)

    def test_apply_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            zshrc = Path(temp_dir) / ".zshrc"
            zshrc.write_text("# user-owned preface\n", encoding="utf-8")
            env = os.environ.copy()
            env["ZSHRC"] = str(zshrc)
            first = subprocess.run(
                [str(INSTALLER), "--apply"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            installed = zshrc.read_text(encoding="utf-8")
            second = subprocess.run(
                [str(INSTALLER), "--apply"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(zshrc.read_text(encoding="utf-8"), installed)
            self.assertEqual(installed.count("# >>> agent-harness auto-mode functions >>>"), 1)
            self.assertEqual(installed.count("# <<< agent-harness auto-mode functions <<<"), 1)
            self.assertIn("already up to date", second.stdout)

    def test_apply_migrates_exact_legacy_unmarked_block(self) -> None:
        legacy = """# user-owned preface

# Agent CLI session modes
claude-auto() {
  command claude --permission-mode auto "$@"
}

codex-auto() {
  command codex -a never -s workspace-write "$@"
}

hclaude-auto() {
  command headroom wrap claude --no-context-tool -- \\
    --permission-mode auto "$@"
}

hcodex-auto() {
  command headroom wrap codex --no-context-tool -- \\
    -a never -s workspace-write "$@"
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            zshrc = Path(temp_dir) / ".zshrc"
            zshrc.write_text(legacy, encoding="utf-8")
            env = os.environ.copy()
            env["ZSHRC"] = str(zshrc)
            result = subprocess.run(
                [str(INSTALLER), "--apply"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = zshrc.read_text(encoding="utf-8")
            self.assertIn("# user-owned preface", installed)
            self.assertNotIn("# Agent CLI session modes", installed)
            installed_lines = installed.splitlines()
            for function_name in (
                "claude-auto",
                "codex-auto",
                "hclaude-auto",
                "hcodex-auto",
            ):
                self.assertEqual(installed_lines.count(f"{function_name}() {{"), 1)
            self.assertEqual(
                installed.count("# >>> agent-harness auto-mode functions >>>"), 1
            )

    def test_apply_preserves_modified_legacy_lookalike(self) -> None:
        custom = """# Agent CLI session modes
claude-auto() {
  command claude --permission-mode plan "$@"
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            zshrc = Path(temp_dir) / ".zshrc"
            zshrc.write_text(custom, encoding="utf-8")
            env = os.environ.copy()
            env["ZSHRC"] = str(zshrc)
            result = subprocess.run(
                [str(INSTALLER), "--apply"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = zshrc.read_text(encoding="utf-8")
            self.assertIn('command claude --permission-mode plan "$@"', installed)
            self.assertEqual(installed.splitlines().count("claude-auto() {"), 2)


if __name__ == "__main__":
    unittest.main()
