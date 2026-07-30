"""Deployment boundary: machine-state hygiene and manifest-driven sync."""
import shutil

from support import *  # noqa: F401,F403


def hooks_path(repo: Path) -> str:
    """What git in `repo` would actually run hooks from, as configured."""
    got = subprocess.run(["git", "-C", str(repo), "config", "--local",
                          "--get", "core.hooksPath"],
                         capture_output=True, text=True)
    return got.stdout.strip()


class MachineStateHygieneTests(unittest.TestCase):
    def test_no_absolute_home_paths_leak_into_tracked_config(self) -> None:
        sources = set()
        for source_rel, _, _ in deployment_manifest_entries():
            source = ROOT / source_rel
            if source.is_dir():
                for current, dirs, files in os.walk(source, followlinks=True):
                    dirs[:] = [name for name in dirs if name != "__pycache__"]
                    for name in files:
                        if name.endswith(".pyc") or name == ".DS_Store":
                            continue
                        sources.add((Path(current) / name).resolve())
            else:
                sources.add(source.resolve())
        self.assertTrue(sources)
        for path in sorted(sources):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            self.assertNotIn("/Users/", text, str(path.relative_to(ROOT)))

    def test_machine_state_files_are_gitignored(self) -> None:
        ignore = read(".gitignore")
        for entry in ("main/claude/mcp_servers.json", "main/codex/config.toml",
                      ".claude/.headroom_wrap_marker.json", "__pycache__/", "*.pyc"):
            self.assertIn(entry, ignore)
        # Confirmed ignored by git itself (exit 0 == path is ignored).
        for path in ("main/claude/mcp_servers.json", "main/codex/config.toml"):
            self.assertEqual(git("check-ignore", path).returncode, 0, path)
        self.assertEqual(
            git("check-ignore", ".claude/.headroom_wrap_marker.json").returncode, 0
        )
        # Root-level agent directories are reserved for project-specific
        # configuration and must not inherit the deployable bundle ignores.
        for path in (".claude/mcp_servers.json", ".codex/config.toml"):
            self.assertEqual(git("check-ignore", path).returncode, 1, path)
        # And not tracked.
        tracked = git("ls-files").stdout.splitlines()
        self.assertNotIn("main/claude/mcp_servers.json", tracked)
        self.assertNotIn("main/codex/config.toml", tracked)

    def test_settings_are_user_owned_and_portable(self) -> None:
        settings = json.loads(read(".claude/settings.json"))
        for key in ("model", "effortLevel", "fallbackModel"):
            self.assertNotIn(key, settings)
        self.assertNotIn("ANTHROPIC_BASE_URL", settings.get("env", {}))
        mcp_text = read(".claude/examples/headroom-mcp.legacy.json")
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
        self.assertEqual(sum("runtime-guard.py\" --gate" in c for c in pre), 1)
        self.assertEqual(sum("runtime-guard.py" in c for c in start), 1)
        self.assertEqual(sum("commit-test-gate.py" in c for c in pre), 1)

    def test_weekly_integrity_outer_timeout_exceeds_its_inner_work(self) -> None:
        # F-06: the SessionStart hook budget must outlast its slowest internal
        # subprocess. When the outer timeout was 15s and one rsync alone was
        # 30s, a drift-heavy run got killed before writing its throttle stamp
        # and silently retried every session, never completing.
        settings = json.loads(read(".claude/settings.json"))
        outer = next(
            h["timeout"]
            for g in settings["hooks"]["SessionStart"] for h in g["hooks"]
            if "weekly-integrity.py" in h["command"]
        )
        source = read(".claude/hooks/weekly-integrity.py")
        inner = [int(m) for m in re.findall(r"timeout=budget\((\d+)\)", source)]
        self.assertGreater(outer, max(inner),
                           "weekly-integrity outer timeout must exceed its "
                           "slowest internal subprocess timeout")
        # outer > max(inner) is not enough on its own: the checks run in
        # sequence, and their caps sum to well over the outer budget, so a
        # drift-heavy run could still be killed before printing findings or
        # writing its stamp. Every subprocess must draw from one monotonic
        # deadline that fits inside the registration.
        self.assertGreater(sum(inner), outer,
                           "if the inner caps no longer oversubscribe the "
                           "outer budget, this guard can be simplified")
        self.assertNotIn("timeout=1", source.replace("timeout=budget(1", "@"))
        deadline = float(re.search(r"BUDGET = ([\d.]+)", source).group(1))
        self.assertLess(deadline, outer,
                        "the global deadline must fit inside the hook timeout")

    def test_headroom_routing_ownership_is_explicit(self) -> None:
        runtime = read(".agents/docs/headroom-runtime.md")
        codex = read(".codex/AGENTS.contract.md")
        setup = read("docs/setup.md")
        for text in (runtime, setup):
            self.assertIn("wrap-first", text)
            self.assertIn("`ANTHROPIC_BASE_URL`", text)
            self.assertIn("`OPENAI_BASE_URL`", text)
            self.assertIn("Codex App", text)
        self.assertIn("This contract owns RTK guidance", codex)
        self.assertIn("headroom wrap claude --no-context-tool", runtime)
        self.assertIn("headroom wrap codex --no-context-tool", runtime)
        self.assertIn("headroom wrap agy", runtime)
        self.assertIn("exit 127", runtime)
        self.assertIn("只證明當下 shell environment", runtime)
        self.assertIn("不代表本 repo 的預設", runtime)
        self.assertIn("Remote Control", runtime)
        self.assertIn("headroom learn", runtime)
        self.assertNotIn("Codex 固定依賴", runtime)
        self.assertNotIn("Codex 使用 `default` profile", runtime)
        for function_name in (
            "agy-auto",
            "hclaude",
            "hcodex",
            "hagy",
            "claude-auto",
            "codex-auto",
            "hclaude-auto",
            "hcodex-auto",
            "hagy-auto",
        ):
            self.assertIn(function_name, setup)
        self.assertIn("--permission-mode auto", runtime)
        self.assertIn("-a on-request -s workspace-write", runtime)
        self.assertIn("--mode accept-edits", runtime)

    def test_commit_gate_blocks_red_suites_and_skips_foreign_repos(self) -> None:
        # Behavioral proof with a planted failure — a gate that cannot catch a
        # deliberate error does not exist. Uses a synthetic repo so the check
        # never recurses into this suite.
        hook = ROOT / "main/claude/hooks/commit-test-gate.py"

        def run_hook(command: str, cwd: str) -> subprocess.CompletedProcess[str]:
            payload = json.dumps({"tool_input": {"command": command}, "cwd": cwd})
            return subprocess.run(
                [sys.executable, str(hook)], input=payload,
                capture_output=True, text=True, timeout=120,
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            # no .claude/tests -> pass through
            self.assertEqual(run_hook("git commit -m x", str(repo)).returncode, 0)
            tests = repo / ".claude" / "tests"
            tests.mkdir(parents=True)
            (tests / "test_red.py").write_text(
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_red(self):\n"
                "        self.fail('planted')\n",
                encoding="utf-8",
            )
            blocked = run_hook("git commit -m x", str(repo))
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("commit blocked", blocked.stderr)
            self.assertEqual(
                run_hook("AGENT_SKIP_TEST_GATE=1 git commit -m x", str(repo)).returncode, 0
            )
            # The escape hatch is a leading shell assignment only — the token
            # inside a commit message (or anywhere else) must not disarm the
            # gate (review F-01).
            msg_form = run_hook(
                "git commit -m 'document AGENT_SKIP_TEST_GATE=1 behavior'", str(repo)
            )
            self.assertEqual(msg_form.returncode, 2)
            # Shell quote concatenation runs a real commit while hiding the
            # word from a plain substring/word match. Reproduced against this
            # gate on 2026-07-28: both forms returned 0 on a red suite.
            for evasion in ("git com''mit -m x", 'git com""mit -m x',
                            "git -C . com''mit -m x",
                            # Splitting both words escaped until 2026-07-29:
                            # the hook always caught it, the settings
                            # prefilter never handed it over.
                            "g'i't com''mit -m x", 'g"i"t com""mit -m x'):
                self.assertEqual(
                    run_hook(evasion, str(repo)).returncode, 2,
                    f"quote-concatenated commit slipped the gate: {evasion}")
            self.assertIn("commit blocked", msg_form.stderr)
            self.assertEqual(run_hook("git status", str(repo)).returncode, 0)
            # Repo-switching forms must gate on the command's target, not cwd
            # (F-01: `git -C` and `cd &&` both bypassed the gate from cwd=/).
            dash_c = run_hook(f"git -C {repo} commit -m x", "/")
            self.assertEqual(dash_c.returncode, 2)
            self.assertIn("commit blocked", dash_c.stderr)
            cd_form = run_hook(f"cd {repo} && git commit -m x", "/")
            self.assertEqual(cd_form.returncode, 2)
            self.assertIn("commit blocked", cd_form.stderr)

            # A backslash-newline continuation is one command; the raw newline
            # must not split `git` from `commit` and slip the gate (F-02).
            cont_form = run_hook("git \\\n  commit -m x", str(repo))
            self.assertEqual(cont_form.returncode, 2)
            self.assertIn("commit blocked", cont_form.stderr)
            # The shell deletes the continuation rather than replacing it with
            # a space, so an intra-word split still runs a real commit. Folding
            # to a space turned it into `com mit` and matched nothing.
            intra_word = run_hook("git com\\\nmit -m x", str(repo))
            self.assertEqual(intra_word.returncode, 2)
            self.assertIn("commit blocked", intra_word.stderr)

            # Expansion is the same evasion one layer later: the payload text
            # is not a commit, the process the shell starts is. Every spelling
            # here is proved to be a real commit by the test below; each of
            # them returned 0 on this red suite until 2026-07-29.
            for evasion in ("EMPTY=; g${EMPTY}it com${EMPTY}mit -m x",
                            "C=commit; git $C -m x",
                            "$(echo git) commit -m x",
                            "`echo git` commit -m x",
                            'E=""; git ${E}commit -m x',
                            "git com$(true)mit -m x"):
                self.assertEqual(
                    run_hook(evasion, str(repo)).returncode, 2,
                    f"expansion-built commit slipped the gate: {evasion}")
            # ...and the price stays narrow. A git command whose subcommand is
            # right there in the text costs nothing even though it expands, so
            # the fix is not "gate everything containing a dollar sign".
            for ordinary in ("git log $(git rev-parse HEAD)",
                             "git diff --stat $(git merge-base main HEAD)",
                             "ls $HOME", "echo ${FOO}"):
                self.assertEqual(
                    run_hook(ordinary, str(repo)).returncode, 0,
                    f"ordinary command paid for the commit gate: {ordinary}")

            # The harness keeps its deployable suite under main/claude/tests.
            # A stale root cache must neither trigger a zero-test false block
            # nor hide the canonical suite.
            (tests / "test_red.py").unlink()
            (tests / "__pycache__").mkdir(exist_ok=True)
            canonical = repo / "main" / "claude" / "tests"
            canonical.mkdir(parents=True)
            canonical_test = canonical / "test_red.py"
            canonical_test.write_text(
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_red(self):\n"
                "        self.fail('canonical planted')\n",
                encoding="utf-8",
            )
            canonical_blocked = run_hook("git commit -m x", str(repo))
            self.assertEqual(canonical_blocked.returncode, 2)
            self.assertIn("main/claude/tests", canonical_blocked.stderr)
            canonical_test.unlink()
            self.assertEqual(run_hook("git commit -m x", str(repo)).returncode, 0)

    def test_every_spelling_that_really_commits_is_blocked(self) -> None:
        """Let the shell decide what a commit is, then require the gate to agree.

        The gate reads text; the shell runs a program. Every earlier hole came
        from asserting that some spelling was an evasion instead of showing it,
        so each command here is first executed in a scratch repo and kept only
        if it actually produced a commit. Whatever survives that filter must be
        blocked on a red suite - the contract is about commits, not about the
        substrings the gate happens to recognize.
        """
        hook = ROOT / "main/claude/hooks/commit-test-gate.py"
        # The spellings whose target the gate cannot name. They have to block
        # for *that* reason: every other target here resolves, and asserting
        # only the exit code would let "blocked because unknown" stand in for
        # "blocked because the suite is red" everywhere.
        unresolvable = {
            'cd "$(echo {repo})" && git commit -m x',
            "git -C {repo_glob} commit -m x",
        }
        # (spelling, environment). `{repo}` stands for the scratch repo's path;
        # a spelling that names its own target is handed to the gate from a cwd
        # that is not a repository at all, so the target resolution has to be
        # what catches it instead of cwd doing the work by accident.
        spellings = [
            ("git commit -m x", {}),                          # plain
            ("git com''mit -m x", {}),                        # quote concatenation
            ("g'i't com''mit -m x", {}),
            ('g"i"t com""mit -m x', {}),
            ("git com\\\nmit -m x", {}),                      # continuation, intra-word
            ("EMPTY=; g${EMPTY}it com${EMPTY}mit -m x", {}),  # parameter expansion
            ("C=commit; git $C -m x", {}),
            ('E=""; git ${E}commit -m x', {}),
            ("$(echo git) commit -m x", {}),                  # command substitution
            ("`echo git` commit -m x", {}),
            ("git com$(true)mit -m x", {}),
            ("true && git commit -m x", {}),                  # operators
            ("false; git commit -m x", {}),
            ('eval "gi""t com""mit -m x"', {}),               # eval
            ("G=git; $G commit -m x", {}),                    # expanded executable
            ("$PRE_GIT commit -m x", {"PRE_GIT": "git"}),     # from the environment
            # The value is itself an expansion, so the gate cannot resolve it
            # from either source: only the structural check is left.
            ("G=$(echo git); $G commit -m x", {}),
            ("R={repo}; git -C \"$R\" commit -m x", {}),      # expanded target
            ("R={repo}; cd \"$R\" && git commit -m x", {}),
            ('git -C "$PRE_REPO" commit -m x', {"PRE_REPO": "{repo}"}),
            ('cd "$PRE_REPO" && git commit -m x', {"PRE_REPO": "{repo}"}),
            # Neither the program nor its argument is in the text, and neither
            # value is in reach: only the structure says what this is.
            ("G=$(printf git); C=$(printf commit); $G $C -m x", {}),
            # Literal executable, and it is the argument that runs.
            ('G=$(printf git); C=$(printf commit); eval "$G $C -m x"', {}),
            # `~` is rewritten by the shell with no expansion character in it,
            # and `git rev-parse` does not rewrite it back.
            ("git -C {tilde_repo} commit -m x", {}),
            ("cd {tilde_repo} && git commit -m x", {}),
            # Unresolvable targets: blocked for that reason, not silently allowed.
            ('cd "$(echo {repo})" && git commit -m x', {}),
            ("git -C {repo_glob} commit -m x", {}),
        ]
        identity = {
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
        }
        # `~` only means anything for a path under HOME, and the platform temp
        # dir is not one, so the tilde spellings get a scratch repo that is.
        with (tempfile.TemporaryDirectory() as temp_dir,
              tempfile.TemporaryDirectory(dir=Path.home(),
                                          prefix=".gate-test-") as home_dir):
            for index, (template, template_env) in enumerate(spellings):
                written = "".join([template, *template_env.values()])
                base = home_dir if "{tilde_repo}" in written else temp_dir
                repo = Path(base) / f"repo{index}"
                repo.mkdir()
                names_target = any(mark in written for mark in
                                   ("{repo}", "{tilde_repo}", "{repo_glob}"))

                def fill(text: str) -> str:
                    return (text
                            .replace("{tilde_repo}",
                                     "~/" + str(repo.relative_to(Path.home()))
                                     if base == home_dir else str(repo))
                            .replace("{repo_glob}", f"{repo}*")
                            .replace("{repo}", str(repo)))

                spelling = fill(template)
                case_env = {name: fill(value)
                            for name, value in template_env.items()}
                subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
                (repo / "f.txt").write_text("x", encoding="utf-8")
                subprocess.run(["git", "-C", str(repo), "add", "f.txt"], check=True)
                subprocess.run(["sh", "-c", spelling], cwd=repo,
                               env={**os.environ, **identity, **case_env},
                               capture_output=True, text=True)
                counted = subprocess.run(
                    ["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
                    capture_output=True, text=True)
                self.assertEqual(counted.stdout.strip(), "1",
                                 f"spelling did not actually commit: {spelling!r}")

                tests = repo / ".claude" / "tests"
                tests.mkdir(parents=True)
                (tests / "test_red.py").write_text(
                    "import unittest\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_red(self):\n"
                    "        self.fail('planted')\n",
                    encoding="utf-8",
                )
                payload = json.dumps({"tool_input": {"command": spelling},
                                      "cwd": temp_dir if names_target else str(repo)})
                blocked = subprocess.run(
                    [sys.executable, str(hook)], input=payload,
                    capture_output=True, text=True, timeout=120,
                    env={**os.environ, **case_env})
                self.assertEqual(blocked.returncode, 2,
                                 f"real commit slipped the gate: {spelling!r}")
                reason = ("could not be resolved" if template in unresolvable
                          else "is RED")
                self.assertIn(reason, blocked.stderr,
                              f"blocked for the wrong reason: {spelling!r}")

    def test_the_git_hook_catches_what_no_text_matching_can(self) -> None:
        """The other boundary: a commit the Bash gate is right not to see.

        `sh release.sh` contains no `git`, no `commit`, and no expansion - the
        command text is honest and says nothing, because the commit is inside
        the script. That is the residue four review rounds kept arriving at, so
        this test asserts both halves: the Bash gate allows it (there is
        nothing there to find) and the commit is refused anyway, by git, in the
        repository it was actually happening in.
        """
        gate = ROOT / "main/claude/hooks/commit-test-gate.py"
        githook = ROOT / "main/claude/githooks/pre-commit"
        identity = {
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
        }
        red = ("import unittest\n"
               "class T(unittest.TestCase):\n"
               "    def test_red(self):\n"
               "        self.fail('planted')\n")
        green = ("import unittest\n"
                 "class T(unittest.TestCase):\n"
                 "    def test_green(self):\n"
                 "        pass\n")

        def commits(repo: Path) -> int:
            counted = subprocess.run(
                ["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
                capture_output=True, text=True)
            return int(counted.stdout.strip()) if counted.returncode == 0 else 0

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            (repo / "main/claude/hooks").mkdir(parents=True)
            (repo / "main/claude/githooks").mkdir(parents=True)
            shutil.copy(gate, repo / "main/claude/hooks/commit-test-gate.py")
            shutil.copy(githook, repo / "main/claude/githooks/pre-commit")
            tests = repo / ".claude" / "tests"
            tests.mkdir(parents=True)
            (tests / "test_red.py").write_text(red, encoding="utf-8")
            (repo / "release.sh").write_text("git commit -m x\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath",
                            "main/claude/githooks"], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)

            spelling = "sh release.sh"
            payload = json.dumps({"tool_input": {"command": spelling},
                                  "cwd": str(repo)})
            seen = subprocess.run([sys.executable, str(gate)], input=payload,
                                  capture_output=True, text=True, timeout=120)
            self.assertEqual(seen.returncode, 0,
                             "the premise changed: the Bash gate now sees this")

            env = {**os.environ, **identity}
            subprocess.run(["sh", "-c", spelling], cwd=repo, env=env,
                           capture_output=True, text=True, timeout=300)
            self.assertEqual(commits(repo), 0, "the git hook let a red suite commit")

            (tests / "test_red.py").write_text(green, encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["sh", "-c", spelling], cwd=repo, env=env,
                           capture_output=True, text=True, timeout=300)
            self.assertEqual(commits(repo), 1, "the git hook blocked a green suite")

            (tests / "test_red.py").write_text(red, encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["sh", "-c", spelling], cwd=repo,
                           env={**env, "AGENT_SKIP_TEST_GATE": "1"},
                           capture_output=True, text=True, timeout=300)
            self.assertEqual(commits(repo), 2, "the escape hatch does not work")

            # A checkout that points git here and then cannot load the shared
            # decision is broken, not opted out.
            (repo / "main/claude/hooks/commit-test-gate.py").unlink()
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["sh", "-c", spelling], cwd=repo, env=env,
                           capture_output=True, text=True, timeout=300)
            self.assertEqual(commits(repo), 2,
                             "the git hook committed without being able to check")

    def test_sync_installs_the_git_side_of_the_commit_gate(self) -> None:
        """A hook nobody points git at is a file, not a gate.

        `core.hooksPath` is repo-local state, so it has to be installed by the
        same command that deploys everything else - otherwise the boundary
        exists in the tree and not in any checkout.
        """
        installer = str(ROOT / "scripts/install-git-hooks.sh")
        hook = ROOT / "main/claude/githooks/pre-commit"
        self.assertTrue(os.access(hook, os.X_OK), "pre-commit is not executable")

        # sync.sh is what a person runs, so the installer has to be on its path
        # and its status has to reach the exit code. The branches themselves are
        # proved below against scratch repos; they cannot be proved through
        # sync.sh, whose REPO is the developer's own checkout by construction.
        sync = read("scripts/sync.sh")
        self.assertIn("scripts/install-git-hooks.sh", sync)
        self.assertIn("\ninstall_git_hooks\n", sync)
        self.assertIn("exit $GIT_HOOK_STATUS", sync)

        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "fresh"
            fresh.mkdir()
            subprocess.run(["git", "init", "-q", str(fresh)], check=True,
                           capture_output=True)
            done = subprocess.run([installer, str(fresh)],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            self.assertEqual(hooks_path(fresh), "main/claude/githooks")
            # Running it twice is what every re-sync does.
            again = subprocess.run([installer, str(fresh)],
                                   capture_output=True, text=True)
            self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
            self.assertEqual(hooks_path(fresh), "main/claude/githooks")

    def test_a_hooks_directory_owned_by_another_tool_fails_the_deployment(self) -> None:
        """Git allows one hooks directory, so a clash cannot be merged away.

        The first version of this warned and returned 0: sync printed a line
        nobody reads and then reported success, leaving a checkout that has the
        policy in its tree and no gate in its git. Overwriting is worse - that
        directory is husky's or someone's - so the remaining honest outcome is
        to leave it alone and fail, which is what the exit code says.
        """
        installer = str(ROOT / "scripts/install-git-hooks.sh")
        with tempfile.TemporaryDirectory() as tmp:
            taken = Path(tmp) / "taken"
            taken.mkdir()
            subprocess.run(["git", "init", "-q", str(taken)], check=True,
                           capture_output=True)
            subprocess.run(["git", "-C", str(taken), "config", "--local",
                            "core.hooksPath", ".husky"], check=True)
            clash = subprocess.run([installer, str(taken)],
                                   capture_output=True, text=True)
            self.assertNotEqual(clash.returncode, 0,
                                "sync reported success without installing the gate")
            self.assertIn("NOT installed", clash.stdout + clash.stderr)
            self.assertEqual(hooks_path(taken), ".husky",
                             "another tool's hooks directory was taken over")

    def test_running_the_suite_does_not_configure_the_developers_checkout(self) -> None:
        """A temporary HOME does not isolate repo-local git config.

        The suite runs a real `sync.sh --apply` as a fixture, and `REPO` is the
        actual checkout no matter what HOME says - so without a guard, running
        the tests silently sets `core.hooksPath` on the developer's repo. That
        is how it was found: the first `--apply` after writing the installer
        reported "already set". The sentinel marks exactly the nested case.
        """
        with tempfile.TemporaryDirectory() as temp_home:
            dry = subprocess.run(
                [str(ROOT / "scripts/sync.sh")], capture_output=True, text=True,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
        self.assertEqual(dry.returncode, 0, dry.stderr + dry.stdout)
        self.assertIn("nested run, leaving core.hooksPath alone", dry.stdout)
        self.assertNotIn("core.hooksPath ->", dry.stdout)

    def test_sync_survives_being_invoked_through_sh(self) -> None:
        """`sh scripts/sync.sh` used to abort halfway, reporting success first.

        macOS `/bin/sh` is bash in POSIX mode, where the process substitution
        the deployment inventory is read with is a syntax error - and bash
        parses as it executes, so the run got through preflight and installed
        `core.hooksPath` before dying on a function it had not read yet. The
        operator saw "preflight: passed" and a syntax error and no deployment.
        `bash -n` cannot see this: the file is valid bash, and it is the
        interpreter that is wrong.

        Asserted end to end rather than by grepping for the guard, because
        POSIX-mode bash still sets BASH_VERSION - the first guard written here
        looked right, matched the shell by name, and never fired.
        """
        with tempfile.TemporaryDirectory() as temp_home:
            dry = subprocess.run(
                ["/bin/sh", str(ROOT / "scripts/sync.sh")],
                capture_output=True, text=True, timeout=300,
                env={**os.environ, "HOME": temp_home,
                     "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"},
            )
        self.assertEqual(dry.returncode, 0, dry.stderr + dry.stdout)
        self.assertNotIn("syntax error", dry.stderr + dry.stdout)
        self.assertIn("dry-run complete", dry.stdout,
                      "sync stopped before the end of its own run")

    def test_a_sync_that_stops_early_cannot_report_success(self) -> None:
        """An interrupted sync used to exit 0, which is worse than the interrupt.

        The `sh` run above aborted mid-file, deployed nothing, and handed its
        caller a 0: the EXIT trap ended with `return 0`, and on an abort that
        never ran a failing command bash exits with whatever the trap leaves.
        Preserving `$?` in the trap does not help - measured on bash 3.2, `$?`
        is 0 on that path - so reaching the last line is the only success
        signal, and `SYNC_COMPLETED` is what carries it.

        Probed by stopping a copy immediately after the trap is installed:
        `exit 0` there is the same shape of failure and, unlike a syntax error,
        survives preflight's own `bash -n` to reach the trap at all.
        """
        anchor = "trap sync_cleanup EXIT\n"
        src = read("scripts/sync.sh")
        self.assertEqual(src.count(anchor), 1, "trap site moved; probe is stale")
        with tempfile.TemporaryDirectory() as tmp:
            probe = Path(tmp) / "sync-probe.sh"
            probe.write_text(src.replace(anchor, anchor + "exit 0\n", 1))
            stopped = subprocess.run(["bash", str(probe)],
                                     capture_output=True, text=True, timeout=60)
        self.assertNotEqual(stopped.returncode, 0,
                            "a sync that stopped early reported success")
        self.assertIn("stopped before finishing", stopped.stdout)

    def test_a_directory_row_cannot_rename_its_deployment_target(self) -> None:
        """rsync reads the source's basename; the manifest's target is ignored.

        A directory source is copied into the *parent* of its target, so a row
        like `main/claude/agents  .claude/role-agents` deploys `~/.claude/
        agents` and never touches the declared path. Nothing downstream
        notices: the parity check repeats the same wrong destination and passes,
        and the deployment inventory records ownership of files that were never
        written, so a later removal retires nothing (2026-07-30 review). File
        rows rename legitimately, which is why the rule is scoped to
        directories.

        Run against a symlink farm over the real checkout with one row edited,
        so this exercises the shipped `validate_manifest` rather than a copy of
        its logic. No row in the tracked manifest renames a directory today,
        asserted first so the fixture cannot pass vacuously.
        """
        rows = [line.split("\t") for line in
                read("scripts/deployment-manifest.tsv").splitlines()
                if line and not line.startswith("#")]
        for row in rows:
            if len(row) == 2 and (ROOT / row[0]).is_dir():
                self.assertEqual(row[0].rsplit("/", 1)[-1], row[1].rsplit("/", 1)[-1],
                                 f"tracked manifest already renames: {row}")

        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "repo"
            (fake / "scripts").mkdir(parents=True)
            for entry in ROOT.iterdir():
                if entry.name != "scripts":
                    (fake / entry.name).symlink_to(entry)
            for entry in (ROOT / "scripts").iterdir():
                if entry.name != "deployment-manifest.tsv":
                    (fake / "scripts" / entry.name).symlink_to(entry)
            doctored = read("scripts/deployment-manifest.tsv").replace(
                "main/claude/agents\t.claude/agents",
                "main/claude/agents\t.claude/role-agents", 1)
            self.assertIn(".claude/role-agents", doctored, "anchor row moved")
            (fake / "scripts" / "deployment-manifest.tsv").write_text(
                doctored, encoding="utf-8")

            refused = subprocess.run(
                ["bash", str(fake / "scripts" / "sync.sh")],
                capture_output=True, text=True, timeout=600,
                env={**os.environ, "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"})
        self.assertNotEqual(refused.returncode, 0, refused.stdout)
        self.assertIn("cannot rename its target", refused.stdout)
        # It has to stop in preflight, before anything is copied.
        self.assertNotIn("preflight: passed", refused.stdout)

    def test_preflight_shows_the_routing_warnings_it_used_to_swallow(self) -> None:
        """A non-fatal warning still has to reach somebody.

        `validate` splits its output deliberately: errors fail the command,
        while a quality floor whose approved routes have no measured score - or
        whose tier minima do not separate - is a WARNING on stdout, because
        making it fatal would let an aging benchmark stop a deployment and the
        predictable response is to weaken the floor until it stops complaining.
        Preflight then ran it as `validate >/dev/null`, which is the other way
        to ignore it: the finding existed and no run anyone performs printed it
        (2026-07-30 review).

        Deploy time is the right surface, not the weekly hook: the state
        changes only when a routing file changes, and this is the gate every
        such change passes. The sibling assertion is
        `test_weekly_integrity_says_nothing_about_a_correctly_deployed_system`,
        which is why the warnings must *not* also become a weekly finding.
        """
        # The current Claude config has unmeasured approved routes, so a real
        # dry-run is a live fixture. Assert that first, or a silently clean
        # config would make this test pass by having nothing to show.
        validate = subprocess.run(
            [str(ROOT / "main/claude/scripts/model-routing"), "validate"],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(validate.returncode, 0, validate.stderr)
        expected = [line for line in validate.stdout.splitlines()
                    if line.startswith("WARNING: ")]
        self.assertTrue(
            expected,
            "no floor-coverage warning to surface; this test needs a fixture "
            "config rather than the live one")

        dry_run = subprocess.run(
            ["bash", str(ROOT / "scripts/sync.sh")],
            capture_output=True, text=True, timeout=600,
            env={**os.environ, "AGENT_HARNESS_PREFLIGHT_ACTIVE": "1"})
        self.assertEqual(dry_run.returncode, 0, dry_run.stdout + dry_run.stderr)
        for warning in expected:
            self.assertIn(f"Claude routing: {warning}", dry_run.stdout)

    def test_the_docs_never_present_one_half_of_the_gate_as_the_whole(self) -> None:
        """Neither boundary is the guarantee on its own, so neither is written alone.

        The Bash gate reads command text and cannot see a commit the text does
        not mention; the git hook sees every commit but only in a checkout that
        points at it. Describing either one by itself reads as a guarantee it
        does not have - which is what the prose did until 2026-07-29 - so the
        pairing is asserted instead of intended.

        The list used to be two hard-coded filenames, which is why a third file
        (`main/claude/README.md`) described the Bash half alone for a day. Every
        tracked doc that names the gate is in scope now; contracts are exempt
        because they are prompts, budgeted separately.
        """
        # Contracts are prompts, budgeted separately. Dated history entries are
        # exempt for the opposite reason: they record what was true on a date,
        # and editing them to match today would falsify the record.
        exempt = ("main/claude/plans/orchestration-history.md",)
        docs = [path for path in tracked_markdown()
                if not path.endswith(".contract.md") and path not in exempt]
        named = [path for path in docs if "commit-test-gate" in read_repo(path)]
        self.assertGreaterEqual(len(named), 3, "the gate is documented somewhere")
        for path in named:
            self.assertIn("pre-commit", read_repo(path),
                          f"{path}: describes the Bash commit gate without the "
                          "git-side gate that covers what text cannot reach")

    def test_the_reviewer_boundary_counts_the_layers_it_lists(self) -> None:
        """A cardinality word and an enumeration are two claims, not one.

        Commit b0b1fdd removed `readonly-bash` from the reviewer read-only
        boundary and left the sentence saying 三層 above a list of two, so the
        doc sent the next reader looking for a layer that no longer exists
        (2026-07-30 review). The same commit left half of an old sentence
        spliced onto a new one in the pipe-test bullet.

        Asserting the number against the list - rather than against a constant
        - keeps this true through a genuine third layer as well as through
        another removal. Parentheticals are stripped first so that rewording an
        explanation cannot break the test; only the enumeration structure and
        the number are load-bearing.
        """
        numerals = {"一": 1, "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5}
        body = read_repo("docs/hook-system.md")
        match = re.search(r"唯讀邊界是(.)層合力：(.*?)。", body, re.DOTALL)
        self.assertIsNotNone(match, "the reviewer boundary sentence moved")
        stated = numerals.get(match.group(1))
        self.assertIsNotNone(stated, f"unparsed count: {match.group(1)!r}")

        listed = re.sub(r"（[^）]*）", "", match.group(2))
        items = [item.strip() for item in listed.split("、") if item.strip()]
        self.assertEqual(
            stated, len(items),
            f"the sentence says {stated} layers and lists {len(items)}: {items}")

        # A named layer has to still exist. `readonly-bash` may appear later in
        # the paragraph as history - that is why only this clause is read.
        for item in items:
            for name in re.findall(r"`([a-z0-9-]+)`", item):
                self.assertTrue(
                    (ROOT / f"main/claude/hooks/{name}.py").exists(),
                    f"the boundary lists `{name}` but no such hook ships")

        # The pipe-test bullet's other half of the same edit.
        self.assertNotIn("確認沒有\n  是 blocked case", body,
                         "spliced sentence from the readonly-bash removal")

    def test_no_doc_sells_a_client_side_gate_as_unconditional(self) -> None:
        """The git hook only runs if the program committing lets it run.

        `--no-verify`, `git -c core.hooksPath=...` and `commit-tree` all skip
        it, and a wrapper script hides every one of them from the Bash gate too.
        The docs claimed "涵蓋所有拼法" until 2026-07-30, which reads as a
        guarantee the machine cannot make; the residue and the layer that does
        close it (CI) have to be named wherever the git-side gate is described.
        """
        overclaims = ("所有拼法", "任何拼法", "不論拼法", "一律涵蓋", "任何 commit")
        for path in tracked_markdown():
            body = read_repo(path)
            if "githooks/pre-commit" not in body:
                continue
            for claim in overclaims:
                self.assertNotIn(claim, body,
                                 f"{path}: '{claim}' promises coverage no "
                                 "client-side hook has")
            # An inventory may name the hook without describing its reach. The
            # disclosure is owed by whoever makes the coverage claim.
            if "涵蓋" not in body and "covers" not in body:
                continue
            self.assertIn("--no-verify", body, path)
            self.assertIn("core.hooksPath", body, path)
            self.assertIn("CI", body,
                          f"{path}: names the residue without the layer that "
                          "closes it")

    def test_commit_gate_runs_the_suite_on_a_modern_interpreter(self) -> None:
        # 2026-07-27: the gate ran the suite on `sys.executable`, i.e. the agent
        # process's `python3`. On a machine where that was 3.9.6 every module
        # died on `import tomllib`, so a green suite reported RED and no commit
        # could land. A planted suite that imports tomllib passes only if the
        # gate resolved >= 3.11; an unusable AGENT_HARNESS_PYTHON must be
        # stepped over rather than blocking, and a floor nothing can meet must
        # say so instead of claiming the suite is red.
        hook = ROOT / "main/claude/hooks/commit-test-gate.py"

        def run_hook(cwd: str, env: dict[str, str] | None = None):
            payload = json.dumps({"tool_input": {"command": "git commit -m x"}, "cwd": cwd})
            return subprocess.run(
                [sys.executable, str(hook)], input=payload,
                capture_output=True, text=True, timeout=120,
                env={**os.environ, **(env or {})},
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            tests = repo / ".claude" / "tests"
            tests.mkdir(parents=True)
            (tests / "test_needs_tomllib.py").write_text(
                "import tomllib, unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_parses(self):\n"
                "        self.assertEqual(tomllib.loads('a = 1'), {'a': 1})\n",
                encoding="utf-8",
            )
            # Resolving the interpreter for `unittest` alone left the suite half
            # upgraded: tests that spawn `#!/usr/bin/env python3` scripts still
            # resolved through PATH onto the old python (this is the shape of
            # the experience-ledger scripts, and it kept the gate red).
            spawned = repo / "spawned-tool"
            spawned.write_text(
                "#!/usr/bin/env python3\n"
                "import tomllib\n"
                "print(tomllib.loads('a = 1')['a'])\n",
                encoding="utf-8",
            )
            spawned.chmod(0o755)
            (tests / "test_spawns_shebang.py").write_text(
                "import subprocess, unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_shebang_child_matches_the_runner(self):\n"
                f"        out = subprocess.run([{str(spawned)!r}],\n"
                "            capture_output=True, text=True)\n"
                "        self.assertEqual(out.returncode, 0, out.stderr)\n"
                "        self.assertEqual(out.stdout.strip(), '1')\n",
                encoding="utf-8",
            )
            self.assertEqual(run_hook(str(repo)).returncode, 0)

            # A pointed-at interpreter that cannot meet the floor is skipped,
            # not obeyed: the override is a hint, not a way to disarm the gate.
            stub = Path(temp_dir) / "too-old"
            stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            stub.chmod(0o755)
            self.assertEqual(
                run_hook(str(repo), {"AGENT_HARNESS_PYTHON": str(stub)}).returncode, 0
            )

            # With nothing able to meet the floor the gate still blocks, but
            # names the interpreter rather than the suite — a subprocess cannot
            # reach this branch because its own `sys.executable` always
            # qualifies, so drive `main` in-process with the search starved.
            import importlib.util
            import io
            from unittest import mock

            spec = importlib.util.spec_from_file_location("commit_test_gate_probe", hook)
            gate = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gate)

            self.assertIsNotNone(gate.suite_interpreter())
            payload = json.dumps(
                {"tool_input": {"command": "git commit -m x"}, "cwd": str(repo)}
            )
            stderr = io.StringIO()
            with mock.patch.object(gate.shutil, "which", return_value=None), \
                    mock.patch.object(gate.sys, "stdin", io.StringIO(payload)), \
                    mock.patch.object(gate.sys, "stderr", stderr):
                self.assertEqual(gate.main(), 2)
            self.assertIn("no Python >=", stderr.getvalue())
            self.assertNotIn("is RED", stderr.getvalue())

    def test_weekly_integrity_reports_drift_in_a_clean_git_managed_claude(self) -> None:
        # A git-managed ~/.claude used to answer drift for the .claude targets
        # by itself, via `git status`. That question is "does this checkout
        # match its own HEAD", which is silent for a clean checkout pinned to
        # an old commit — precisely the stale deployment worth catching. Parity
        # against the source checkout must run for those targets regardless.
        hook = ROOT / "main/claude/hooks/weekly-integrity.py"
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            agents = home / ".claude" / "agents"
            agents.mkdir(parents=True)
            # Committed and clean, but the content does not match the source.
            (agents / "explore.md").write_text("stale\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(home / ".claude"), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(home / ".claude"), "add", "-A"], check=True)
            subprocess.run(
                ["git", "-C", str(home / ".claude"), "-c", "user.email=t@t",
                 "-c", "user.name=t", "commit", "-qm", "stale"],
                check=True, env={**os.environ, "AGENT_SKIP_TEST_GATE": "1"},
            )
            status = subprocess.run(
                ["git", "-C", str(home / ".claude"), "status", "--porcelain"],
                capture_output=True, text=True)
            self.assertEqual(status.stdout.strip(), "",
                             "fixture must be clean, or it proves nothing")
            result = subprocess.run(
                [sys.executable, str(hook)], capture_output=True, text=True,
                timeout=120,
                env={**os.environ, "HOME": str(home),
                     "AGENT_HARNESS_REPO": str(ROOT)},
            )
            self.assertIn(".claude/agents", result.stdout,
                          "clean-but-stale git-managed ~/.claude reported no "
                          f"drift for a manifest target:\n{result.stdout}")

    def test_commit_gate_command_prefilters_non_commit_calls(self) -> None:
        # F-03: the PreToolUse gate command must skip the python interpreter
        # entirely for Bash payloads that can carry no commit at all, so
        # ordinary commands do not pay a per-call process spawn (measured
        # 25 ms). A stub hook drops a marker whenever it actually runs.
        # The prefilter matches a normalized copy of the payload - quotes,
        # backslashes and `n` deleted - because `g'i't com''mit` contains
        # neither bare word, and `*git*` alone therefore let it through
        # untouched while the hook behind it was already able to catch it
        # (reproduced 2026-07-29). Deleting characters can only bring a match
        # closer, never hide one, and neither `git` nor `commit` contains any
        # deleted character, so the normalization is monotone.
        settings = json.loads(read(".claude/settings.json"))
        pre = [h["command"] for g in settings["hooks"]["PreToolUse"] for h in g["hooks"]]
        command = next(c for c in pre if "commit-test-gate.py" in c)
        with tempfile.TemporaryDirectory() as temp_home:
            hooks_dir = Path(temp_home) / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            marker = Path(temp_home) / "ran"
            (hooks_dir / "commit-test-gate.py").write_text(
                "import pathlib, sys\n"
                f"pathlib.Path({str(marker)!r}).write_text('x')\n"
                "cmd = __import__('json').load(sys.stdin)['tool_input']['command']\n"
                "sys.exit(2 if 'commit' in cmd else 0)\n",
                encoding="utf-8",
            )
            env = {**os.environ, "HOME": temp_home}

            def run_gate(command_text: str) -> subprocess.CompletedProcess[str]:
                payload = json.dumps({"tool_input": {"command": command_text}})
                return subprocess.run(["sh", "-c", command], input=payload,
                                      capture_output=True, text=True, env=env)

            # Non-commit: exits 0 and never spawns the interpreter.
            self.assertEqual(run_gate("ls -la").returncode, 0)
            self.assertFalse(marker.exists())
            # Commit: the gate runs and its exit code propagates.
            self.assertEqual(run_gate("git commit -m x").returncode, 2)
            self.assertTrue(marker.exists())
            # Every spelling the shell still runs as a commit must reach the
            # hook, which is the layer that can normalize it. Splitting *both*
            # words (`g'i't com''mit`) is the form the old `*commit*|*git*`
            # prefilter dropped outright.
            for evasion in ("git com''mit -m x", "g'i't com''mit -m x",
                            "g\"i\"t com\"\"mit -m x",
                            "git com\\\nmit -m x", "g'i't com\\\nmit -m x",
                            # An expansion leaves nothing for a `case` glob to
                            # recognize - deleting `$`, `{` and `}` from
                            # `g${EMPTY}it` yields `gEMPTYit` - so the prefilter
                            # stops trying to classify these and hands every
                            # payload carrying an expansion to the hook, which
                            # can (2026-07-29).
                            "EMPTY=; g${EMPTY}it com${EMPTY}mit -m x",
                            "C=commit; git $C -m x",
                            "$(echo git) commit -m x",
                            "`echo git` commit -m x"):
                marker.unlink(missing_ok=True)
                run_gate(evasion)
                self.assertTrue(
                    marker.exists(),
                    f"prefilter dropped a real commit before the hook: {evasion!r}")
            # The handover stays a prefilter: a payload with neither a git-ish
            # word nor an expansion still costs no interpreter spawn.
            for ordinary in ("ls -la", "python3 -m unittest", "echo hello"):
                marker.unlink(missing_ok=True)
                self.assertEqual(run_gate(ordinary).returncode, 0)
                self.assertFalse(marker.exists(), ordinary)


if __name__ == '__main__':
    unittest.main()
