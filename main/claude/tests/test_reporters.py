"""Tests for the tools that only report.

Split out of `test_mechanisms.py` on 2026-09-08 because that file held
150 of 462 tests (32.5%) against a 33% ceiling, and the guard that
reports it says to split at a seam rather than raise the constant.

The seam is what the subject *does*: `test_mechanisms.py` keeps gates,
dispatch, traps and surfaces - things that block, route or record - and
this file takes the tools that compute a number and print it. Every one
of them exits 0 by design, which is exactly why their tests belong
together: for a reporter, "it ran" is not the property under test.
"""
import ast
import hashlib
import shutil
import time
import uuid

from support import *  # noqa: F401,F403




class VersionAttestationTests(unittest.TestCase):
    """A sentence claiming a dated local check is behavioural evidence, and it
    was the only kind this repo had no mechanism for. Two of them were wrong on
    2026-08-10: the runtime guide said the machine ran Headroom 0.34.0 while it
    ran 0.33.0, and `RTK.md` said rtk 0.45.0 while the only rtk here was 0.42.4
    (the number came off `brew info`, which prints a formula's version directly
    above `Not installed`).

    So this class is the instrument's own negative control. Half of it proves
    the scanner fires on those two exact shapes; the other half proves it stays
    quiet on the four shapes that made its first draft unusable. Both halves are
    load-bearing - a version of this check that reported twenty findings, of
    which eighteen were percentages and IP addresses, would be read once."""

    def _module(self):
        import importlib.util
        path = ROOT / "scripts" / "evidence-check.py"
        spec = importlib.util.spec_from_file_location("evidence_check", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_it_fires_on_the_two_claims_that_were_actually_wrong(self) -> None:
        module = self._module()
        guide = "2026-08-10 本機查核: CLI 與 proxy 都是 `headroom-ai 0.34.0`."
        self.assertIn(("headroom", "0.34.0"), module.attributions_in(guide))
        self.assertEqual(
            "differs", module.verdict_for("0.34.0", "0.33.0", is_floor=False))

        rtk = "`rtk find … -not` still fails this way (verified against rtk 0.45.0)."
        self.assertIn(("rtk", "0.45.0"), module.attributions_in(rtk))
        self.assertEqual(
            "differs", module.verdict_for("0.45.0", "0.42.4", is_floor=False))

    def test_it_stays_quiet_on_the_shapes_that_are_not_claims(self) -> None:
        module = self._module()
        # Every one of these produced a "difference" in the first draft, which
        # attributed any number on a line to any tool the line mentioned.
        for line in (
            "Headroom saved 56.28% of input tokens, up from 55.69%.",
            "add Headroom with --proxy-url http://127.0.0.1:8787",
            "Pilotfish v1.3.10 蒸餾結果; Headroom 另見 runtime guide",
            "reserving GPT-5.6 for judgment; codex routes stay pinned",
        ):
            with self.subTest(line=line):
                self.assertEqual([], module.attributions_in(line))

    def test_a_floor_is_not_a_stale_attestation(self) -> None:
        # `需要 Claude Code 2.1.207 以上版本` differs from the local version for
        # as long as the requirement stands. Reported as a discrepancy it would
        # appear on every run forever, which is how a report teaches people to
        # skip it.
        module = self._module()
        line = "1. `verifier` 需要 Claude Code 2.1.207 以上版本."
        self.assertIn(("claude code", "2.1.207"), module.attributions_in(line))
        self.assertTrue(module.FLOOR.search(line))
        self.assertEqual(
            "floor-met", module.verdict_for("2.1.207", "2.1.226", is_floor=True))
        self.assertEqual(
            "floor-unmet", module.verdict_for("2.1.207", "2.1.99", is_floor=True))

    def test_a_pinned_condition_is_exempt_but_a_local_check_is_not(self) -> None:
        # `pinned` covers a version frozen by what the line describes: the build
        # a finished batch was probed against, the release a cited paper read.
        # The asymmetry is the point - a doc's own "checked on <date>, CLI was X"
        # stays unexempt, because that is the shape the 2026-08-20 Headroom drift
        # hid in.
        module = self._module()
        condition = "Every row probed on 2026-08-12 against Claude Code 2.1.226"
        self.assertIn(("claude code", "2.1.226"), module.attributions_in(condition))
        self.assertFalse(module.NOT_A_LIVE_CLAIM.search(condition))
        self.assertTrue(module.NOT_A_LIVE_CLAIM.search(
            condition + " <!-- pinned 2026-08-21 -->"))

        local = "2026-08-14 本機查核: CLI 是 `headroom-ai 0.35.0`"
        self.assertFalse(module.NOT_A_LIVE_CLAIM.search(local))

    def test_a_retracted_claim_is_exempt_only_with_a_dated_marker(self) -> None:
        # The 2026-08-20 Headroom round retracted two version claims and left
        # the wrong sentences standing, because the evidence tier records what
        # was checked including what was overturned. Both halves matter: the
        # marker has to silence the retracted line, and the same line without it
        # has to still fire - an exemption that fires on prose alone would be a
        # way to hide a stale version rather than to record a corrected one.
        module = self._module()
        claim = "~~2026-08-14 本機查核: CLI 是 `headroom-ai 0.35.0`~~"
        self.assertIn(("headroom", "0.35.0"), module.attributions_in(claim))
        self.assertFalse(module.NOT_A_LIVE_CLAIM.search(claim))

        marked = claim + " <!-- retracted 2026-08-20 -->"
        self.assertTrue(module.NOT_A_LIVE_CLAIM.search(marked))

        # Undated, and a bare mention of the word, stay unexempt: the marker is
        # a record, not a switch.
        for near_miss in (
            claim + " <!-- retracted -->",
            claim + " (retracted)",
            claim + " <!-- retracted 2026-08 -->",
        ):
            with self.subTest(line=near_miss):
                self.assertFalse(module.NOT_A_LIVE_CLAIM.search(near_miss))

    def test_a_truncated_claim_still_matches_the_release_it_names(self) -> None:
        # Prose writes `headroom 0.34`; the binary answers `0.34.0`. Treating
        # that as a difference would bury the real ones.
        module = self._module()
        self.assertEqual("match", module.verdict_for("0.34", "0.34.0", False))
        self.assertEqual("differs", module.verdict_for("0.33", "0.34.0", False))

    def test_a_zh_tw_floor_and_a_dated_title_are_not_stale_attestations(self) -> None:
        """Two shapes added 2026-08-17, both from the same review of a real report.

        Half of that run's discrepancies were sentences that are still true.
        `起` is zh-TW's "from <version> onwards", the exact counterpart of the
        English floors this class already covers, so `Headroom v0.34 起已移除 …`
        was filed as a permanent finding about a correct sentence. And a dated
        section title names the version it was *about*: rewriting
        `#### 2026-08-10 查核結果 (Headroom 0.34 升級)` to today's number destroys
        the record it exists to keep.

        The dividing line is what the guard below asserts, and it is the one that
        matters: exempting *headings* is not exempting dated lines. A dated claim
        in prose is precisely what this instrument is for - the date is what makes
        going stale checkable - so the exemption is keyed on the heading marker
        and the anchor link, never on the presence of a date.
        """
        module = self._module()
        floor = "Headroom v0.34 起已移除 CLI context tools; wrapper 不再傳入舊參數."
        self.assertIn(("headroom", "0.34"), module.attributions_in(floor))
        self.assertTrue(module.FLOOR.search(floor))
        self.assertEqual(
            "floor-met", module.verdict_for("0.34", "0.35.0", is_floor=True))

        for line in (
            "#### 2026-08-10 查核結果 (Headroom 0.34 升級): 同一個失效換了一層皮",
            "- [2026-08-10 查核結果 (Headroom 0.34 升級)](landing-log.md"
            "#2026-08-10-查核結果-headroom-034-升級)",
        ):
            with self.subTest(line=line[:40]):
                self.assertTrue(module.HISTORY.search(line))

        # The guard. Same date, same tool, same wrong number - still a claim.
        claim = "2026-08-10 本機查核: CLI 與 proxy 都是 `headroom-ai 0.34.0`."
        self.assertIsNone(
            module.HISTORY.search(claim),
            "a dated prose attestation must stay checkable; exempting it would "
            "make the date - the thing that makes staleness detectable - into "
            "the way to avoid being checked")

    def test_only_a_floor_is_measured_against_this_machine(self) -> None:
        """The narrowing of 2026-08-21, and why it is structural.

        This check existed for one shape - a document attesting a local version
        while the machine ran another - and machine-local version records left
        the guidance tier the same day by policy. What remained were upstream
        versions, which a local binary cannot adjudicate, and on a shared
        repository an exact version that is right where it was written reads as
        a discrepancy everywhere else.

        Prose sniffing was tried and abandoned: the research row that records
        upstream and *not* this machine matched a locality pattern on the very
        word it uses to disclaim locality. So the rule is the line's shape, not
        its wording, and both directions are asserted here.
        """
        module = load_module("evidence_check", ROOT / "scripts" / "evidence-check.py")
        self.assertFalse(hasattr(module, "LOCALITY"),
                         "prose sniffing came back; a regex cannot separate a "
                         "claim from its negation")

        verdicts = {row["verdict"] for row in module.audit_versions()}
        self.assertFalse(
            {"match", "differs"} & verdicts,
            "an exact version was compared against this machine; only floors are")
        self.assertIn("not-local", verdicts,
                      "upstream versions must be named as such, not dropped")
        self.assertIn("floor-met", verdicts,
                      "floors are the portable claim and must still be checked")

        # A floor the machine meets exactly is a met floor, not an attestation.
        self.assertEqual(module.verdict_for("0.45", "0.45.0", True), "floor-met")
        self.assertEqual(module.verdict_for("9.9", "0.45.0", True), "floor-unmet")

    def test_it_reports_and_never_fails(self) -> None:
        # Same contract as the rest of this script: a stale attestation is a
        # fact to weigh. Made fail-closed, the cheapest way to stay green would
        # be to stop writing the date next to what was checked.
        finished = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "evidence-check.py"), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(0, finished.returncode, finished.stderr)
        report = json.loads(finished.stdout)
        self.assertIn("versions", report)
        self.assertIn("attestations", report)
        for row in report["versions"]:
            self.assertIn(row["verdict"], {
                # `not-local` joined on 2026-08-21: an exact version in a
                # tracked document is about upstream or about history, and a
                # local binary adjudicates neither. Only floors are compared.
                "match", "differs", "floor-met", "floor-unmet", "unprobeable",
                "not-local"})



class UpstreamPinReportTests(unittest.TestCase):
    """`upstream-recheck.sh` verifies the bytes a SHA pins, so it stays green
    when upstream moves - that is the design. Nothing asked the other question
    until 2026-08-21, when `mattpocock/skills` turned out to be twelve commits
    past its recorded pin and only a manual look found it.

    The registry is derived from the attributions rather than listed, so the two
    properties worth holding are that it reads all three shapes those files use,
    and that a fetch it could not complete never reads as "not moved"."""

    SCRIPT = ROOT / "scripts/upstream-pin-report.py"

    def _module(self):
        return load_module("upstream_pin_report", self.SCRIPT)

    def test_it_reads_every_shape_an_attribution_states_its_source_in(self) -> None:
        shapes = {
            # `**Source**:` plus `**Reviewed commit**:`
            "a": "- **Source**: <https://github.com/one/alpha>\n"
                 "- **Reviewed commit**: `" + "1" * 40 + "`\n",
            # a bare URL on its own line plus `- Commit:` as a link
            "b": "https://github.com/two/beta\n\n- Commit: [`" + "2" * 40 + "`]"
                 "(https://github.com/two/beta/commit/" + "2" * 40 + ")\n",
            # the zh-TW shape: `- 專案：[name](url)` plus `- 蒸餾自：`
            "c": "- 專案：[gamma](https://github.com/three/gamma)\n"
                 "- 蒸餾自：`" + "3" * 40 + "`（2026-07-18 的 master）\n",
            # names no repository at all - must be skipped, not guessed at
            "d": "Adapted from a talk. No repository, no commit.\n",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name, body in shapes.items():
                (root / name).mkdir()
                (root / name / "ATTRIBUTION.md").write_text(body, encoding="utf-8")
            # the same upstream shipped twice, as task-observer really is
            (root / "twin").mkdir()
            (root / "twin" / "ATTRIBUTION.md").write_text(shapes["b"], encoding="utf-8")

            found = self._module().parse_attributions(root)
            by_repo = {e["repo"]: e for e in found}
            self.assertEqual(sorted(by_repo),
                             ["one/alpha", "three/gamma", "two/beta"],
                             "a shape went unread, or the sourceless one was guessed at")
            self.assertEqual(by_repo["one/alpha"]["pin"], "1" * 40)
            self.assertEqual(by_repo["three/gamma"]["pin"], "3" * 40)
            self.assertEqual(sorted(by_repo["two/beta"]["skills"]), ["b", "twin"],
                             "one upstream shipped twice must be one entry")

    def test_it_also_reads_pins_the_research_index_states_without_an_attribution(self) -> None:
        """`Nanako0129/sepia` moved 86 commits and released four versions in
        five days, and on 2026-09-05 nothing here noticed until someone read
        the date on its row in the research README. It has no ATTRIBUTION -
        nothing distilled from it has reached `main/` yet - and this report was
        derived from ATTRIBUTION files alone. A pin that lives only in the
        currency table is still a pin.

        Only 上游 rows count. A 同業 row also carries a full SHA (eli5's path
        commit), and comparing that against a whole repository would report
        every unrelated plugin's move as ours to read. A row that restates an
        attributed pin joins that entry rather than becoming a second upstream.
        """
        module = self._module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a").mkdir()
            (root / "a" / "ATTRIBUTION.md").write_text(
                "- **Source**: <https://github.com/one/alpha>\n"
                "- **Reviewed commit**: `" + "1" * 40 + "`\n", encoding="utf-8")
            index = root / "README.md"
            rows = (
                "| 來源 | 類別 | 現況 | 查核日 | 備註 |\n|---|---|---|---|---|\n"
                "| one/alpha | 上游 | marketplace pin `" + "1" * 40 + "` | 2026-09-05 | attributed |\n"
                "| `four/delta` 與上游論文 | 上游 + 研究 | pin `" + "4" * 40 + "` (head) | 2026-09-05 | no attribution yet |\n"
                "| `five/epsilon` 的 `thing` | 同業 | path 最後 commit 仍是 `" + "5" * 40 + "` | 2026-09-05 | surveyed |\n"
            )
            index.write_text(rows, encoding="utf-8")

            by_repo = {e["repo"]: e for e in module.collect(root, index)}
            self.assertEqual(sorted(by_repo), ["four/delta", "one/alpha"],
                             "an 上游 row without an ATTRIBUTION is a pin; a 同業 row is not")
            self.assertEqual(by_repo["four/delta"]["pin"], "4" * 40)
            self.assertEqual(by_repo["four/delta"]["skills"], [])
            self.assertEqual(by_repo["four/delta"]["sites"], ["research-index"])
            self.assertEqual(by_repo["one/alpha"]["skills"], ["a"])
            self.assertEqual(sorted(by_repo["one/alpha"]["sites"]),
                             ["attribution", "research-index"],
                             "a row restating an attributed pin joins that entry")

            # Take the row away and the index-only upstream goes with it: the
            # report is derived, so the table is the only place to list it.
            index.write_text(rows.replace("four/delta", "four-delta"), encoding="utf-8")
            self.assertEqual(sorted(e["repo"] for e in module.collect(root, index)),
                             ["one/alpha"])

    def test_a_peer_row_that_pins_a_head_is_tracked_too(self) -> None:
        """The discriminator is the spelling, not the 類別 column.

        `affaan-m/ecc` was surveyed on 2026-09-08 and pinned at a head commit,
        and nothing would have noticed it moving: this report read 上游 rows
        only, and a 同業 row was skipped even when it carried a full SHA. The
        reason for that skip was real but narrower than the rule - eli5's SHA
        is the last commit touching one path, so comparing it against the whole
        repository would report every unrelated plugin's move as ours to read.

        So the rule is the sentence the row writes, not the column beside it.
        `pin ``<sha>``` means "this is the commit to compare the repository
        against"; a SHA introduced any other way (`path 最後 commit 仍是`)
        means something else and is left alone. That makes the spelling a
        contract a row author can meet deliberately, which the 類別 column
        never was - it says what a source is *to us*, not what its SHA means.
        """
        module = self._module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index = root / "README.md"
            index.write_text(
                "| 來源 | 類別 | 現況 | 查核日 | 備註 |\n|---|---|---|---|---|\n"
                "| `six/zeta` | 同業 | pin `" + "6" * 40 + "` (head, 2026-09-07) | 2026-09-08 | surveyed, head pinned |\n"
                "| `five/epsilon` 的 `thing` | 同業 | path 最後 commit 仍是 `" + "5" * 40 + "` | 2026-09-05 | a path, not a head |\n",
                encoding="utf-8")

            by_repo = {e["repo"]: e for e in module.collect(root, index)}
            self.assertEqual(
                sorted(by_repo), ["six/zeta"],
                "a peer row that pins a head is tracked; one that names a path "
                "commit is not, and the column is not what tells them apart")
            self.assertEqual(by_repo["six/zeta"]["pin"], "6" * 40)
            self.assertEqual(by_repo["six/zeta"]["sites"], ["research-index"])

            # Mutation in reverse: respell the head pin as a path commit and it
            # drops out, which is what makes the spelling load-bearing rather
            # than incidental.
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "pin `" + "6" * 40 + "` (head, 2026-09-07)",
                    "path 最後 commit 仍是 `" + "6" * 40 + "`"),
                encoding="utf-8")
            self.assertEqual([], module.collect(root, index))

    def test_the_real_index_tracks_the_peer_it_pinned_and_not_the_one_it_did_not(self) -> None:
        """The fixture above proves the rule; this proves it is switched on.

        Both rows are 同業. One is in because it pins a head, the other is out
        because its SHA is a path commit - and if the two ever swap places
        without this failing, the rule stopped being enforced on the tree it
        was written for.
        """
        module = self._module()
        found = {e["repo"] for e in module.parse_research_index(
            ROOT / "docs/research/README.md")}
        self.assertIn("affaan-m/ecc", found,
                      "the peer whose row pins a head is not being watched")
        self.assertNotIn("anthropics/claude-plugins-community", found,
                         "a path commit must not be compared against a whole repo")

    def test_a_move_says_where_it_moved(self) -> None:
        """A commit count cannot separate a rule change from a regenerated chart.

        On 2026-08-24 one upstream read `MOVED +3` and all three commits were a
        bot refreshing an SVG under `assets/`; the other read `MOVED +5` and the
        commits were under `skills/`. Only one of those was worth a diff, and
        the report said the same thing about both. The compare response already
        carries the file list, so the answer costs no extra request.
        """
        module = self._module()
        body = {
            "ahead_by": 3,
            "commits": [{"sha": "a" * 40,
                         "commit": {"committer": {"date": "2026-08-22T00:00:00Z"}}}],
            "files": [{"filename": "skills/engineering/tdd/SKILL.md"},
                      {"filename": "skills/productivity/grilling/SKILL.md"},
                      {"filename": "assets/readme/chart.svg"},
                      {"filename": ".gitignore"}],
        }
        summary = module.summarise(body)
        self.assertEqual(summary["state"], "moved")
        self.assertEqual(summary["areas"],
                         {"skills/": 2, "assets/": 1, ".gitignore": 1},
                         "top-level areas are what separate a rule change from "
                         "a regenerated asset")

        # No file list is "cannot say where", not "moved nowhere": an upstream
        # whose compare response omits files must not read as untouched.
        quiet = module.summarise({"ahead_by": 1, "commits": []})
        self.assertEqual(quiet["areas"], {})
        self.assertEqual(quiet["state"], "moved")

    def test_a_move_the_last_check_already_read_is_not_reported_as_new(self) -> None:
        """`MOVED` is measured against the pin, and the pin is not the last look.

        Measured on 2026-09-11: seven upstreams read `MOVED`, and three of them
        - `mattpocock/skills` +2, `rebelytics/one-skill-to-rule-them-all` +1,
        `Nanako0129/pilotfish` +19 - were moves whose diffs were already
        classified, with the dispositions sitting in their own ATTRIBUTION files
        and in the currency table. Nothing in the report said so, and the round
        that day nearly re-read all three. The pin stays where it is on purpose
        for a marketplace upstream, so this is not a stale pin; it is the report
        answering a question nobody asked twice.

        The check date is already parsed out of the currency table and the head
        commit's date already arrives in the compare response, so this compares
        two things the report is holding rather than fetching anything new.

        Two properties, and the second is the one that bites. The head's date
        decides, not the first new commit's: `Nanako0129/sepia` that day had its
        first new commit on the check date itself and its head five days later,
        so keying on the range's start would have called genuinely new material
        already-seen. And a missing date answers `None`, never `False` - the
        same distinction the unreachable branch exists for.
        """
        module = self._module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a").mkdir()
            (root / "a" / "ATTRIBUTION.md").write_text(
                "- **Source**: <https://github.com/seven/eta>\n"
                "- **Reviewed commit**: `" + "7" * 40 + "`\n", encoding="utf-8")
            index = root / "README.md"
            index.write_text(
                "| 來源 | 類別 | 現況 | 查核日 | 備註 |\n|---|---|---|---|---|\n"
                "| seven/eta | 上游 | pin `" + "7" * 40 + "` | 2026-09-10 | attributed too |\n"
                "| `eight/theta` | 上游 | pin `" + "8" * 40 + "` | 2026-09-05 | index only |\n",
                encoding="utf-8")
            by_repo = {e["repo"]: e for e in module.collect(root, index)}
            self.assertEqual(by_repo["eight/theta"].get("checked"), "2026-09-05")
            self.assertEqual(
                by_repo["seven/eta"].get("checked"), "2026-09-10",
                "the check date must survive a row joining an attribution entry, "
                "which is the case every distilled upstream is in")

        # sepia's shape: the range opens on the check date and ends after it.
        straddles = module.summarise({"ahead_by": 36, "commits": [
            {"sha": "a" * 40, "commit": {"committer": {"date": "2026-09-05T09:00:00Z"}}},
            {"sha": "b" * 40, "commit": {"committer": {"date": "2026-09-10T09:00:00Z"}}}]})
        self.assertEqual(straddles["head_date"], "2026-09-10",
                         "the head's date decides, not the range's first commit")
        self.assertIs(True, module.unseen({**straddles, "checked": "2026-09-05"}))

        # pilotfish's shape: the whole range predates the last look.
        classified = module.summarise({"ahead_by": 19, "commits": [
            {"sha": "c" * 40, "commit": {"committer": {"date": "2026-08-22T09:00:00Z"}}},
            {"sha": "d" * 40, "commit": {"committer": {"date": "2026-08-28T09:00:00Z"}}}]})
        self.assertIs(False, module.unseen({**classified, "checked": "2026-09-10"}))

        # No check date, or no head date: say so rather than claiming it is old.
        self.assertIsNone(module.unseen({**classified}))
        self.assertIsNone(module.unseen({"checked": "2026-09-10"}))

    def test_a_fetch_it_cannot_complete_is_never_reported_as_current(self) -> None:
        """The distinction the whole report rests on. Offline this takes the
        network-error branch and online the 404 branch; both must land on
        `unreachable`, because `current` would say an upstream had not moved
        when nobody asked it."""
        result = self._module().moved(
            "agent-harness-no-such-org-9f3a/no-such-repo", "0" * 40)
        self.assertEqual(result["state"], "unreachable")
        self.assertNotEqual(result["state"], "current")



class MachineStateCheckTests(unittest.TestCase):
    """It exists because the denial-log bleed was found by hand and nothing would
    have found the next one. So the property that matters is that it notices a
    write - a version that always printed "no change" would have looked correct
    every day of the twelve this ran undetected."""

    SCRIPT = ROOT / "scripts/machine-state-check.py"

    def _run(self, tree: Path, command: str):
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), "--trees", str(tree),
             "--command", command, "--json"], capture_output=True, text=True)

    def test_it_names_the_file_a_command_wrote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tree = Path(temp_dir)
            (tree / "kept.txt").write_text("x", encoding="utf-8")
            report = json.loads(self._run(tree, f"echo hi > {tree}/leaked.txt").stdout)
            self.assertEqual([Path(p).name for p in report["added"]], ["leaked.txt"])
            self.assertEqual(report["changed"], [])
            self.assertEqual(report["removed"], [])

    def test_a_rewrite_that_keeps_the_size_is_still_a_change(self) -> None:
        """The version that shipped first compared size and whole-second mtime,
        so a state file rewritten to the same length inside one second was
        invisible - a counter or a fixed-width timestamp has exactly that shape.
        Small files are compared by content now, which also means a touch that
        changes nothing does not read as a change."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tree = Path(temp_dir)
            target = tree / "state.json"
            target.write_text('{"n": 9}', encoding="utf-8")
            report = json.loads(
                self._run(tree, f"printf '{{\"n\": 8}}' > {target}").stdout)
            self.assertEqual([Path(p).name for p in report["changed"]],
                             ["state.json"], "a same-size rewrite went unseen")

            target.write_text('{"n": 8}', encoding="utf-8")
            touched = json.loads(self._run(tree, f"touch {target}").stdout)
            self.assertEqual(touched["changed"], [],
                             "a touch with no content change reported as one")

    def test_a_command_that_writes_nothing_reports_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tree = Path(temp_dir)
            (tree / "kept.txt").write_text("x", encoding="utf-8")
            report = json.loads(self._run(tree, "true").stdout)
            self.assertEqual(report["added"], [])
            self.assertEqual(report["changed"], [])
            self.assertEqual(report["removed"], [])
            self.assertEqual(report["watched"], 1)



class ResidentPoolReportTests(unittest.TestCase):
    """The coverage figure this report exists to print is the one that can
    silently invert.

    `resident-pool-report` splits the installed pool into what this repo's
    budgets reach and what nothing reaches, and the 2026-08-18 measurement put
    that at about a sixth. The split is derived from the deployment manifest,
    so a shipped skill crosses the line on the commit that ships it - and a
    change to how the manifest names its targets would move every skill into
    "unmanaged" while the script still exits 0 and still prints a table. That
    failure looks exactly like a healthy report of a much worse number, which
    is why the derivation is asserted rather than the number.
    """

    def setUp(self) -> None:
        self.module = load_module(
            "resident_pool_report", ROOT / "scripts" / "resident-pool-report.py")

    def test_the_managed_set_is_read_from_the_manifest(self) -> None:
        expected = {
            line.split("\t")[1].rsplit("/", 1)[-1]
            for line in read("scripts/deployment-manifest.tsv").splitlines()
            if line and not line.startswith("#")
            and len(line.split("\t")) >= 2
            and line.split("\t")[1].startswith(".claude/skills/")}
        self.assertTrue(expected, "the manifest ships no Claude skill; fixture is vacuous")
        self.assertEqual(expected, self.module.managed_names())

    def test_a_skill_outside_the_manifest_counts_as_unmanaged(self) -> None:
        """The one classification the headline depends on, over a synthetic pool.

        Reading the real `~/.claude/skills` would make this assert whatever the
        machine happens to hold, which is the opposite of what a suite should
        do with machine state.
        """
        shipped = sorted(self.module.managed_names())[0]
        with tempfile.TemporaryDirectory() as tmp:
            pool = Path(tmp)
            for name, description in ((shipped, "a shipped one"),
                                      ("not-ours", "installed from elsewhere")):
                (pool / name).mkdir()
                (pool / name / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: {description}\n---\n\nbody\n",
                    encoding="utf-8")
            original = self.module.POOL
            try:
                self.module.POOL = pool
                rows = {row["name"]: row for row in self.module.measure()["skills"]}
            finally:
                self.module.POOL = original
        self.assertEqual("repo-managed", rows[shipped]["origin"])
        self.assertEqual("unmanaged", rows["not-ours"]["origin"])
        # Only `name` and `description` are resident; the body must not be counted.
        self.assertEqual(
            self.module.word_count("not-ours installed from elsewhere"),
            rows["not-ours"]["words"])

    def test_it_reports_and_never_fails(self) -> None:
        # Report-only for the reason in its docstring: the skills it cannot
        # cap are not this repo's files. A gate here would fail a commit
        # because the user installed something, and the cheapest way back to
        # green would be uninstalling it.
        finished = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "resident-pool-report.py"),
             "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(0, finished.returncode, finished.stderr)
        report = json.loads(finished.stdout)
        self.assertTrue(report["floor"], "the total must not claim to be the whole")
        self.assertEqual(
            set(), {row["origin"] for row in report["skills"]}
            - {"repo-managed", "project", "unmanaged"})



class DenialReportTests(unittest.TestCase):
    """The reader is the half that was missing for twelve days, so the property
    worth pinning is that it reads the file the gates actually write to - a
    report aimed at a stale path would print `no denials recorded` forever and
    look exactly like a quiet week."""

    SCRIPT = ROOT / "scripts/denial-report.py"

    def _run(self, log: Path):
        return subprocess.run(
            [sys.executable, str(self.SCRIPT)],
            env={**os.environ, "AGENT_DENIAL_LOG": str(log)},
            capture_output=True, text=True)

    def test_it_reads_the_log_the_gates_write_to(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "denials.jsonl"
            log.write_text("\n".join(json.dumps(row) for row in (
                {"ts": "2026-08-19T01:00:00+00:00", "gate": "leaf-redispatch",
                 "reason": "leaf-tried-to-dispatch", "session_id": "s"},
                {"ts": "2026-08-21T02:00:00+00:00", "gate": "runtime-guard",
                 "reason": "runtime-too-old-or-unknown"},
            )) + "\n", encoding="utf-8")
            result = self._run(log)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("2 row(s)", result.stdout)
            self.assertIn("leaf-redispatch / leaf-tried-to-dispatch", result.stdout)
            # One row predates the isolation date and one does not, so the
            # provenance line has to split them rather than label the file.
            self.assertIn("1 row(s) predate", result.stdout)

    def test_a_missing_or_broken_log_reports_instead_of_failing(self) -> None:
        """Report-only means report-only: an unreadable line is a skipped line,
        not an exit code. A reader that can fail becomes a gate by accident."""
        with tempfile.TemporaryDirectory() as temp_dir:
            absent = self._run(Path(temp_dir) / "nothing.jsonl")
            self.assertEqual(absent.returncode, 0, absent.stderr)
            self.assertIn("no denials recorded", absent.stdout)

            broken = Path(temp_dir) / "broken.jsonl"
            broken.write_text('{"ts": "2026-08-21T00:00:00+00:00", "gate": "g", '
                              '"reason": "r"}\nnot json\n[1, 2]\n',
                              encoding="utf-8")
            result = self._run(broken)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("2 unparseable line(s)", result.stdout)
            self.assertIn("1 row(s)", result.stdout)



class ReportOnlyToolTests(unittest.TestCase):
    def test_the_readme_counts_the_report_only_tools_it_lists(self) -> None:
        """A stated count beside a list is the cheapest thing in this repo to
        get wrong, and the fail-closed gate count proved it: one document said
        五 for three weeks after the sixth gate landed, because nothing tied the
        numeral to the inventory (2026-08-20).

        The same shape sits in the README - a numeral, then a fenced block of
        report-only tools. Derived from the block rather than pinned, so adding
        a fifth tool without touching the numeral fails here.

        Not derived from `scripts/` itself: "always exits 0" would sweep in
        `contract-operator-delta.py`, which is corroboration inside the
        contract-slimming flow rather than one of these. The list is curated by
        purpose, so the block is the inventory and this only holds the count to
        it.
        """
        readme = read_repo("README.md")
        # Runs past the current count on purpose. The map stopped at 七 and the
        # inventory reached 九 on 2026-08-21, at which point the guard could not
        # read the numeral at all and failed with "the README states how many
        # there are" - a guard that goes blind rather than red is the worse
        # failure, because the message points at the document instead of itself.
        # Past 十 the numeral is two characters, so the pattern is an
        # alternation with the longer form first: a character class would match
        # the 十 in 十一 and read eleven as ten - a guard that silently reads the
        # wrong number is worse than one that cannot read at all. Widened when
        # the inventory reached 十一 on 2026-08-24, which is what the previous
        # note here said it would take.
        numerals = {"三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8,
                    "九": 9, "十": 10, "十一": 11, "十二": 12, "十三": 13,
                    "十四": 14, "十五": 15}
        # Longest first, so 十一 never matches as 十.
        alternation = "|".join(sorted(numerals, key=len, reverse=True))
        stated = re.search(rf"({alternation})支只報不擋的工具", readme)
        self.assertIsNotNone(stated, "the README states how many there are")

        block = re.search(r"支只報不擋的工具.*?```bash\n(.*?)```", readme, re.S)
        self.assertIsNotNone(block, "the tools are listed in a fenced block")
        listed = re.findall(r"^(scripts/[\w.-]+)", block.group(1), re.MULTILINE)
        self.assertEqual(
            numerals[stated.group(1)], len(listed),
            f"README says {stated.group(1)}支 but lists {len(listed)}: {listed}")
        for script in listed:
            self.assertTrue((ROOT / script).exists(), script)

        # And every other guidance document stating the count is held to the
        # same block. Matching stops before the noun, because the copy that went
        # stale used a different one: the README said 四支只報不擋的工具 while
        # docs/architecture/harness-engineering.md said 四支只報不擋的腳本, and
        # `codename-gloss-report.py` was in neither list - so both numerals
        # agreed with each other and both were one short (2026-08-20).
        for path in guidance_markdown():
            if path == "README.md":
                continue
            for numeral in re.findall(rf"({alternation})支只報不擋",
                                      read_repo(path)):
                self.assertEqual(
                    numerals[numeral], len(listed),
                    f"{path}: says {numeral}支 but the README block lists "
                    f"{len(listed)}")


class ReportCadenceTests(unittest.TestCase):
    """Every script under `scripts/` says when it is meant to be read.

    `docs/hook-system.md` already records what happens to an instrument nobody
    reads: the denial log ran for twelve days and grew to 35,856 rows of which
    three were real. That was fixed at the writing end. The reading end was
    still nobody's job - on 2026-09-08 one of twenty-one scripts had a
    scheduled reader (`contract-operator-delta`, from the git hook), and the
    rest waited for somebody to remember.

    The fix is not to schedule all of them. Twenty-one reports in one weekly
    summary is the same failure wearing a different hat, and
    `docs/research/resident-context-options.md` settles the general form: a
    cost this layer does not pay is reported, not gated. So each script states
    a `Read:` line naming the **event** that should send someone to it.

    An event, not a mood. `Read: on demand` is exactly the declaration that
    guarantees nothing ever triggers it, so it is spelled `Read: never`
    instead - and a script whose honest answer is `never` is a deletion
    candidate, which is the finding this rule exists to produce rather than a
    failure to avoid.
    """

    SCRIPTS = ROOT / "scripts"
    MARKER = "Read:"
    # Only the contentless spellings. A bare "whenever" is fine - "whenever a
    # budget number is about to be raised" names an event - and a proxy that
    # cannot tell those apart would be rejecting the good ones to look strict.
    VAGUE = ("on demand", "as needed", "when needed", "if curious",
             "whenever needed", "whenever you")

    def script_files(self) -> list:
        return sorted(path for path in self.SCRIPTS.iterdir()
                      if path.suffix in (".py", ".sh"))

    def cadence(self, path) -> str:
        """The `Read:` comment on the line after the shebang.

        The position is the rule, not a convenience. Review found the first
        landing in two wrong places at once: inside a `.py` module docstring,
        where `--help` printed it with argparse collapsing the paragraph
        breaks, and at the tail of whatever comment block came last in a
        `.sh` file - for `sync.sh` a technical aside about bash re-exec. A
        declaration nobody sees is the defect this rule exists to prevent, so
        the check is narrow enough to catch a repeat.
        """
        lines = path.read_text(encoding="utf-8").splitlines()[:3]
        for line in lines:
            stripped = line.lstrip("#").strip()
            if stripped.startswith(self.MARKER):
                return stripped[len(self.MARKER):].strip()
        return ""

    def test_no_declaration_leaks_into_help_output(self) -> None:
        """`Read:` is maintainer metadata, not usage text.

        Sixteen scripts pass `__doc__` to argparse, so a line inside the module
        docstring reaches every `--help`.
        """
        for path in self.script_files():
            if path.suffix != ".py":
                continue
            source = path.read_text(encoding="utf-8")
            first = source.find(chr(34) * 3)
            if first == -1:
                continue
            close = source.find(chr(34) * 3, first + 3)
            self.assertNotIn(
                self.MARKER, source[first:close],
                f"{path.name}: the declaration is inside the module docstring, "
                "so it prints in --help; put it above as a comment")

    def test_every_script_declares_when_it_should_be_read(self) -> None:
        missing = [path.name for path in self.script_files() if not self.cadence(path)]
        self.assertEqual(
            [], missing,
            "no `Read:` line in: " + ", ".join(missing)
            + " - a report with no reading trigger is one nobody will run")

    def test_a_cadence_names_an_event_rather_than_a_mood(self) -> None:
        """`on demand` is the answer that makes the rule vacuous, so it is not
        an allowed spelling. `never` is - and it is a deletion candidate."""
        for path in self.script_files():
            cadence = self.cadence(path).lower()
            for vague in self.VAGUE:
                self.assertNotIn(
                    vague, cadence,
                    f"{path.name}: `Read: {cadence}` names no event. If nothing "
                    "would ever send someone to it, say `Read: never` and treat "
                    "it as a deletion candidate")

    def test_the_deletion_candidates_are_listed_where_someone_will_see_them(self) -> None:
        """A `never` that only exists in a docstring is not a finding yet."""
        never = [path.name for path in self.script_files()
                 if self.cadence(path).lower().startswith("never")]
        if not never:
            return
        listed = read_repo("docs/research/mechanism-evidence-map.md")
        for name in never:
            self.assertIn(
                name, listed,
                f"{name} declares `Read: never` but no inventory names it as a "
                "deletion candidate")
