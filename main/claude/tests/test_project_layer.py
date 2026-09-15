"""Project layer: a per-repository fact bundle rendered from one facts file.

`main/project/README.md` (the plan it was written for retired 2026-09-15). The global layer under HOME
carries authority - roles, dispatch, verification, gates - and travels with
the person. The project layer carries facts about one repository - its test
command, its truth sources, its traps, its fastest refuting check - and
travels with the repository. The boundary is one rule with a local
measurement behind it: injected sentences override contract rules (0/27 in
the position experiments), so a project layer that said what to do next
would steer the global harness rather than inform it.

Three pins come first (P0) and were red before any implementation existed:
the two manifests share no source, the templates carry no authority
vocabulary, and the fixed text of a template has a budget - it is resident in
every session opened in that repository.
"""
import os
import subprocess
import sys
import tempfile

from support import *  # noqa: F401,F403

SCRIPT = ROOT / "scripts/project-init.py"
PROJECT_MANIFEST = ROOT / "scripts/project-manifest.tsv"
TEMPLATES = ("main/project/CLAUDE.project.md", "main/project/AGENTS.project.md")
FACTS_EXAMPLE = ROOT / "main/project/facts.example.toml"
SLOT = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")
START, END = "<!-- agent-harness:start -->", "<!-- agent-harness:end -->"

#: Authority vocabulary. A project block that names a role, a dispatch skill,
#: a record marker or a dispatch verb has started to say what to do next,
#: which is the global contract's sentence. Matched as whole words, case
#: insensitive; a fact may still say "review" or "check", because a fact about
#: how to check this repository is exactly what the layer is for.
FORBIDDEN = (
    "executor", "mech-executor", "plan-verifier", "verifier",
    "security-reviewer", "security-executor", "explore",
    "[LEAF_DISPATCH]", "[LEAF_RESULT]",
    "baton-dispatch", "provider-routing", "leaf-dispatch", "experience-ledger",
    "delegate", "dispatch", "subagent", "sub-agent", "workflow",
)

#: Fixed text of a template, slots removed, in `word_count` units. Measured
#: then padded about two percent, the same ratchet the resident contracts use.
#: The rendered block in a real repository is larger by whatever the facts
#: are; that ceiling is set in P2 after one real fill, not guessed here.
FIXED_TEXT_CEILING = {"CLAUDE.project.md": 72, "AGENTS.project.md": 42}  # measured 70 / 41 on 2026-09-10

FILLED_FACTS = '''project = "widget"
test_command = "make test"
lint_command = "make lint"
shortest_loop = "mypy on the touched module, then the one test that names it"
truth_sources = ["docs/schema.md for the wire format", "the tracker issue for intended behaviour"]
traps = ["tests need PG_URL or they hang for 30s"]
review_lenses = ["serialization boundaries", "retry and idempotency"]
'''


def project_manifest_entries() -> list[tuple[str, str, str]]:
    rows = []
    for raw in PROJECT_MANIFEST.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        fields = raw.split("\t")
        rows.append((fields[0], fields[1], fields[2] if len(fields) > 2 else ""))
    return rows


def run_init(repo, *args, home) -> subprocess.CompletedProcess:
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(repo), *args],
        capture_output=True, text=True, timeout=60, env=env, cwd=ROOT)


def slots(text: str) -> set[str]:
    return set(SLOT.findall(text))


class ProjectLayerBoundaryTests(unittest.TestCase):
    """P0: the three pins, red before P1 existed."""

    def test_project_manifest_shares_no_source_with_the_global_manifest(self) -> None:
        """One file deployed by two manifests is one file with two owners.

        The global manifest maps sources to HOME; the project manifest maps
        sources to a repository. Targets may spell the same relative path
        (`.codex/AGENTS.md` under HOME and `AGENTS.md` under a repo are different
        files the client reads together); sources may not overlap, or a change to
        one surface silently ships to the other.
        """
        project = {source for source, _, _ in project_manifest_entries()}
        self.assertTrue(project, "the project manifest names no sources")
        shared = project & {source for source, _ in deployment_manifest()}
        self.assertEqual(sorted(shared), [], "sources deployed by both manifests")

    def test_project_manifest_rows_are_merge_block_and_sources_exist(self) -> None:
        for source, target, mode in project_manifest_entries():
            with self.subTest(source=source):
                self.assertTrue((ROOT / source).is_file(), f"{source}: no such source")
                self.assertEqual(mode, "merge-block",
                                 "a project contract lands as a fenced block "
                                 "inside a file the team may already own")
                self.assertFalse(target.startswith("/"), "targets are repo-relative")

    def test_templates_carry_facts_not_authority(self) -> None:
        pattern = re.compile(
            "|".join(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])"
                     for word in FORBIDDEN), re.IGNORECASE)
        for relative in (*TEMPLATES, "main/project/facts.example.toml"):
            with self.subTest(template=relative):
                found = sorted({m.group(0).lower()
                                for m in pattern.finditer(read_repo(relative))})
                self.assertEqual(
                    found, [],
                    f"{relative} names authority vocabulary; a project block "
                    "states facts and leaves the verbs to the global contract")

    def test_both_templates_ask_the_same_facts(self) -> None:
        """Twin parity for the project layer: one facts file, two renderings."""
        asked = {relative: slots(read_repo(relative)) for relative in TEMPLATES}
        first, second = (asked[t] for t in TEMPLATES)
        self.assertTrue(first, "the Claude template has no slots")
        self.assertEqual(first, second, "the two templates ask different facts")
        import tomllib
        keys = set(tomllib.loads(FACTS_EXAMPLE.read_text(encoding="utf-8")))
        self.assertEqual(first, keys,
                         "the facts skeleton and the templates disagree on "
                         "which facts exist")

    def test_template_fixed_text_stays_within_budget(self) -> None:
        for relative in TEMPLATES:
            name = relative.rsplit("/", 1)[1]
            fixed = SLOT.sub("", read_repo(relative))
            with self.subTest(template=name):
                self.assertLessEqual(
                    word_count(fixed), FIXED_TEXT_CEILING[name],
                    f"{name}: fixed text grew past its ceiling; this block is "
                    "resident in every session of every repository that "
                    "installs it, so displace before adding")

    def test_init_refuses_a_repo_whose_targets_are_home_managed(self) -> None:
        """Pointing init at HOME would give every session on the machine a root
        CLAUDE.md. The path-overlap check does not catch it since the target moved
        to the repository root, so the refusal is explicit."""
        with tempfile.TemporaryDirectory() as home:
            finished = run_init(home, "--apply", home=home)
            self.assertEqual(finished.returncode, 5, finished.stdout + finished.stderr)
            self.assertFalse((Path(home) / "CLAUDE.md").exists())
            self.assertFalse((Path(home) / ".agent-harness").exists())

    def test_init_refuses_this_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            finished = run_init(ROOT, home=home)
            self.assertEqual(finished.returncode, 5, finished.stdout + finished.stderr)
            self.assertFalse((ROOT / ".agent-harness").exists())


class ProjectInitTests(unittest.TestCase):
    """P1: dry-run by default, facts in one place, fenced blocks, verify."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.home = base / "home"
        self.repo = base / "repo"
        self.home.mkdir()
        self.repo.mkdir()
        self.facts = self.repo / ".agent-harness" / "facts.toml"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def fill(self) -> None:
        self.facts.parent.mkdir(parents=True, exist_ok=True)
        self.facts.write_text(FILLED_FACTS, encoding="utf-8")

    def init(self, *args) -> subprocess.CompletedProcess:
        return run_init(self.repo, *args, home=self.home)

    def test_init_refuses_two_targets_that_resolve_to_one_file(self) -> None:
        """Three of this workspace's five contract-bearing repositories keep
        `CLAUDE.md` as a symlink to `AGENTS.md` - baccarat, colorgame and
        roulette, the whole nexus family. So both manifest targets land on one
        inode, and measured on 2026-09-11 that was silent: `--apply` printed
        two successful writes, exited 0, and left a single block behind. The
        Codex one, because the second render found the first inside the markers
        and replaced it. A Claude session following the link then reads the
        Codex wording of every fact, and nothing anywhere says so.

        Refused rather than merged. Which client's block should win is not a
        question this script gets to answer quietly, and the repository that
        chose the symlink is the one that knows why.
        """
        self.fill()
        (self.repo / "AGENTS.md").write_text("# team contract\n", encoding="utf-8")
        (self.repo / "CLAUDE.md").symlink_to("AGENTS.md")
        finished = self.init("--apply")
        self.assertEqual(5, finished.returncode, finished.stdout + finished.stderr)
        self.assertIn("same file", finished.stderr.lower())
        self.assertEqual("# team contract\n",
                         (self.repo / "AGENTS.md").read_text(encoding="utf-8"),
                         "a refusal that already wrote is not a refusal")

    def test_dry_run_writes_nothing(self) -> None:
        self.fill()
        finished = self.init()
        self.assertEqual(finished.returncode, 0, finished.stderr)
        self.assertIn("[dry-run]", finished.stdout)
        self.assertEqual(sorted(p.name for p in self.repo.iterdir()), [".agent-harness"])

    def test_first_apply_writes_the_facts_skeleton_and_stops(self) -> None:
        finished = self.init("--apply")
        self.assertEqual(finished.returncode, 3, finished.stdout + finished.stderr)
        self.assertTrue(self.facts.is_file(), "the skeleton is the first thing written")
        self.assertFalse((self.repo / "CLAUDE.md").exists(),
                         "no contract renders before the facts are filled")
        self.assertFalse((self.repo / "AGENTS.md").exists())

    def test_unfilled_facts_are_refused_by_name(self) -> None:
        self.init("--apply")  # writes the skeleton
        finished = self.init("--apply")
        self.assertEqual(finished.returncode, 3)
        for key in ("test_command", "truth_sources"):
            self.assertIn(key, finished.stdout + finished.stderr,
                          "an unfilled fact is named, not counted")

    def test_apply_renders_both_blocks_and_preserves_team_text(self) -> None:
        self.fill()
        (self.repo / "CLAUDE.md").write_text(
            "# Team rules\n\nAlways run the linter.\n", encoding="utf-8")
        finished = self.init("--apply")
        self.assertEqual(finished.returncode, 0, finished.stdout + finished.stderr)
        claude = (self.repo / "CLAUDE.md").read_text(encoding="utf-8")
        agents = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(claude.startswith("# Team rules"), "team text stays first")
        self.assertIn("Always run the linter.", claude)
        for text, label in ((claude, "CLAUDE.md"), (agents, "AGENTS.md")):
            with self.subTest(file=label):
                self.assertEqual(text.count(START), 1)
                self.assertEqual(text.count(END), 1)
                self.assertIn("make test", text)
                self.assertIn("PG_URL", text)
                self.assertNotIn("{{", text, "an unfilled slot shipped")

    def test_apply_is_idempotent_and_verify_is_green(self) -> None:
        self.fill()
        self.init("--apply")
        before = {p: p.read_text(encoding="utf-8")
                  for p in (self.repo / "CLAUDE.md", self.repo / "AGENTS.md")}
        second = self.init("--apply")
        self.assertEqual(second.returncode, 0, second.stderr)
        for path, text in before.items():
            self.assertEqual(path.read_text(encoding="utf-8"), text,
                             f"{path.name} changed on an idempotent re-apply")
        verify = self.init("--verify")
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)

    def test_verify_reports_a_hand_edit_inside_the_block(self) -> None:
        self.fill()
        self.init("--apply")
        path = self.repo / "AGENTS.md"
        path.write_text(path.read_text(encoding="utf-8").replace("make test", "make quick"),
                        encoding="utf-8")
        verify = self.init("--verify")
        self.assertEqual(verify.returncode, 1, verify.stdout + verify.stderr)
        self.assertIn("AGENTS.md", verify.stdout + verify.stderr)

    def test_verify_reports_not_installed(self) -> None:
        self.fill()
        verify = self.init("--verify")
        self.assertEqual(verify.returncode, 4, verify.stdout + verify.stderr)

    def test_verify_reports_a_block_past_the_rendered_ceiling(self) -> None:
        """P2 set the ceiling from the first real fill (238 words); a block that
        outgrows it is a resident cost every session in that repository pays,
        so `--verify` treats it as drift rather than printing a warning nobody
        reads. `--apply` still lands it and says so."""
        fat = FILLED_FACTS.replace(
            'traps = ["tests need PG_URL or they hang for 30s"]',
            "traps = [" + ", ".join(f'"trap number {i} with enough words to matter here"'
                                     for i in range(30)) + "]")
        self.facts.parent.mkdir(parents=True, exist_ok=True)
        self.facts.write_text(fat, encoding="utf-8")
        applied = self.init("--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertIn("ceiling", applied.stderr, "apply warns when it writes a fat block")
        verify = self.init("--verify")
        self.assertEqual(verify.returncode, 1, verify.stdout + verify.stderr)
        self.assertIn("ceiling", verify.stdout)

    def test_a_fact_value_carrying_a_slot_is_residue(self) -> None:
        self.facts.parent.mkdir(parents=True, exist_ok=True)
        self.facts.write_text(FILLED_FACTS.replace('"make lint"', '"{{lint}}"'),
                              encoding="utf-8")
        finished = self.init("--apply")
        self.assertEqual(finished.returncode, 3, finished.stdout + finished.stderr)
        self.assertFalse((self.repo / "AGENTS.md").exists(),
                         "residue must be refused before anything is written")


if __name__ == "__main__":
    unittest.main()
